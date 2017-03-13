"""Amavis handlers."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa.admin import models as admin_models
from modoboa.lib import parameters

from . import models


@receiver(signals.post_save, sender=admin_models.AliasRecipient)
def on_aliasrecipient_created(sender, instance, **kwargs):
    """Create amavis record for the new alias recipient.

    FIXME: how to deal with distibution lists ?
    """
    condition = (
        parameters.get_admin("MANUAL_LEARNING") == "no" or
        parameters.get_admin("USER_LEVEL_LEARNING") == "no" or
        not instance.r_mailbox or
        instance.alias.type != "alias")
    if condition:
        return

    policy = models.Policy.objects.filter(
        policy_name=instance.r_mailbox.full_address).first()
    if policy:
        # Use mailbox policy for this new alias. We update or create
        # to handle the case where an account is being replaced by an
        # alias (when it is disabled).
        email = instance.alias.address
        models.Users.objects.update_or_create(
            email=email,
            defaults={"policy": policy, "fullname": email, "priority": 7}
        )
