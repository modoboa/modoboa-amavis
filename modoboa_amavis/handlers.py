# -*- coding: utf-8 -*-

"""Amavis handlers."""

from __future__ import unicode_literals

from django.db.models import signals
from django.dispatch import receiver
from django.template import Context, Template
from django.urls import reverse
from django.utils.translation import ugettext as _

from modoboa.admin import models as admin_models, signals as admin_signals
from modoboa.core import signals as core_signals
from modoboa.lib import signals as lib_signals
from modoboa.parameters import tools as param_tools
from . import forms
from .lib import (
    create_user_and_policy, create_user_and_use_policy, delete_user,
    delete_user_and_policy, update_user_and_policy
)
from .models import Policy, Users
from .sql_connector import SQLconnector


@receiver(core_signals.extra_user_menu_entries)
def menu(sender, location, user, **kwargs):
    """Add extra menu entry."""
    if location == "top_menu":
        return [
            {"name": "quarantine",
             "label": _("Quarantine"),
             "url": reverse("modoboa_amavis:index")}
        ]
    return []


@receiver(signals.post_save, sender=admin_models.Domain)
def manage_domain_policy(sender, instance, **kwargs):
    """Create user and policy when a domain is added."""
    if kwargs.get("created"):
        create_user_and_policy("@{0}".format(instance.name))
    else:
        update_user_and_policy(
            "@{0}".format(instance.oldname),
            "@{0}".format(instance.name)
        )


@receiver(signals.pre_delete, sender=admin_models.Domain)
def on_domain_deleted(sender, instance, **kwargs):
    """Delete user and policy for domain."""
    delete_user_and_policy("@{0}".format(instance.name))


@receiver(signals.post_save, sender=admin_models.DomainAlias)
def on_domain_alias_created(sender, instance, **kwargs):
    """Create user and use domain policy for domain alias."""
    if not kwargs.get("created"):
        return
    create_user_and_use_policy(
        "@{0}".format(instance.name),
        "@{0}".format(instance.target.name)
    )


@receiver(signals.pre_delete, sender=admin_models.DomainAlias)
def on_domain_alias_deleted(sender, instance, **kwargs):
    """Delete user for domain alias."""
    delete_user("@{0}".format(instance.name))


@receiver(signals.post_save, sender=admin_models.Mailbox)
def on_mailbox_modified(sender, instance, **kwargs):
    """Update amavis records if address has changed."""
    condition = (
        not param_tools.get_global_parameter("manual_learning") or
        not hasattr(instance, "old_full_address") or
        instance.full_address == instance.old_full_address)
    if condition:
        return
    try:
        user = Users.objects.select_related("policy").get(
            email=instance.old_full_address)
    except Users.DoesNotExist:
        return
    full_address = instance.full_address
    user.email = full_address
    user.policy.policy_name = full_address[:32]
    user.policy.sa_username = full_address
    user.policy.save()
    user.save()


@receiver(signals.pre_delete, sender=admin_models.Mailbox)
def on_mailbox_deleted(sender, instance, **kwargs):
    """Clean amavis database when a mailbox is removed."""
    if not param_tools.get_global_parameter("manual_learning"):
        return
    delete_user_and_policy("@{0}".format(instance.full_address))


@receiver(signals.post_save, sender=admin_models.AliasRecipient)
def on_aliasrecipient_created(sender, instance, **kwargs):
    """Create amavis record for the new alias recipient.

    FIXME: how to deal with distibution lists ?
    """
    conf = dict(param_tools.get_global_parameters("modoboa_amavis"))
    condition = (
        not conf["manual_learning"] or not conf["user_level_learning"] or
        not instance.r_mailbox or
        instance.alias.type != "alias")
    if condition:
        return
    policy = Policy.objects.filter(
        policy_name=instance.r_mailbox.full_address).first()
    if policy:
        # Use mailbox policy for this new alias. We update or create
        # to handle the case where an account is being replaced by an
        # alias (when it is disabled).
        email = instance.alias.address
        Users.objects.update_or_create(
            email=email,
            defaults={"policy": policy, "fullname": email, "priority": 7}
        )


@receiver(signals.pre_delete, sender=admin_models.Alias)
def on_mailboxalias_deleted(sender, instance, **kwargs):
    """Clean amavis database when an alias is removed."""
    if not param_tools.get_global_parameter("manual_learning"):
        return
    if instance.address.startswith("@"):
        # Catchall alias, do not remove domain entry accidentally...
        return
    aliases = [instance.address]
    Users.objects.filter(email__in=aliases).delete()


@receiver(core_signals.extra_static_content)
def extra_static_content(sender, caller, st_type, user, **kwargs):
    """Send extra javascript."""
    condition = (
        user.role == "SimpleUsers" or
        st_type != "js" or
        caller != "domains")
    if condition:
        return ""
    tpl = Template("""<script type="text/javascript">
$(document).bind('domform_init', function() {
    activate_widget.call($('#id_spam_subject_tag2_act'));
});
</script>
""")
    return tpl.render(Context({}))


@receiver(core_signals.get_top_notifications)
def check_for_pending_requests(sender, include_all, **kwargs):
    """Check if release requests are pending."""
    request = lib_signals.get_request()
    condition = (
        param_tools.get_global_parameter("user_can_release") or
        request.user.role == "SimpleUsers")
    if condition:
        return []

    nbrequests = SQLconnector(user=request.user).get_pending_requests()
    if not nbrequests:
        return [{"id": "nbrequests", "counter": 0}] if include_all \
            else []

    url = reverse("modoboa_amavis:index")
    url += "#listing/?viewrequests=1"
    return [{
        "id": "nbrequests", "url": url, "text": _("Pending requests"),
        "counter": nbrequests, "level": "danger"
    }]


@receiver(admin_signals.extra_domain_forms)
def extra_domain_form(sender, user, domain, **kwargs):
    """Return domain config form."""
    if not user.has_perm("admin.view_domains"):
        return []
    return [{
        "id": "amavis", "title": _("Content filter"),
        "cls": forms.DomainPolicyForm,
        "formtpl": "modoboa_amavis/domain_content_filter.html"
    }]


@receiver(admin_signals.get_domain_form_instances)
def fill_domain_instances(sender, user, domain, **kwargs):
    """Return domain instance."""
    if not user.has_perm("admin.view_domains"):
        return {}
    return {"amavis": domain}
