# -*- coding: utf-8 -*-

"""
Amavis frontend template tags.
"""

from __future__ import unicode_literals

from django import template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from .. import constants, lib

register = template.Library()


@register.simple_tag
def viewm_menu(user, mail_id, rcpt):
    """Menu displayed within the viewmail action."""
    entries = [
        {"name": "back",
         "url": "javascript:history.go(-1);",
         "img": "fa fa-arrow-left",
         "class": "btn-primary",
         "label": _("Back")},
        {"name": "release",
         "img": "fa fa-check",
         "class": "btn-success",
         "url": (
             reverse("modoboa_amavis:mail_release", args=[mail_id]) +
             ("?rcpt=%s" % rcpt if rcpt else "")),
         "label": _("Release")},
        {"name": "delete",
         "class": "btn-danger",
         "img": "fa fa-trash",
         "url": (
             reverse("modoboa_amavis:mail_delete", args=[mail_id]) +
             ("?rcpt=%s" % rcpt if rcpt else "")),
         "label": _("Delete")},
        {"name": "headers",
         "class": "btn-default",
         "url": reverse("modoboa_amavis:headers_detail", args=[mail_id]),
         "label": _("View full headers")},
    ]

    if lib.manual_learning_enabled(user):
        entries.insert(3, {
            "name": "process",
            "img": "fa fa-cog",
            "menu": [
                {"name": "mark-as-spam",
                 "label": _("Mark as spam"),
                 "url": reverse(
                     "modoboa_amavis:mail_mark_as_spam", args=[mail_id]
                 ) + ("?rcpt=%s" % rcpt if rcpt else ""),
                 "extra_attributes": {
                     "data-mail-id": mail_id
                 }},
                {"name": "mark-as-ham",
                 "label": _("Mark as non-spam"),
                 "url": reverse(
                     "modoboa_amavis:mail_mark_as_ham", args=[mail_id]
                 ) + ("?rcpt=%s" % rcpt if rcpt else ""),
                 "extra_attributes": {
                     "data-mail-id": mail_id
                 }}
            ]
        })

    menu = render_to_string("common/buttons_list.html",
                            {"entries": entries, "extraclasses": "pull-left"})

    entries = [{"name": "close",
                "url": "javascript:history.go(-1);",
                "img": "icon-remove"}]
    menu += render_to_string(
        "common/buttons_list.html",
        {"entries": entries, "extraclasses": "pull-right"}
    )

    return menu


@register.simple_tag
def viewm_menu_simple(user, mail_id, rcpt, secret_id=""):
    release_url = "{0}?rcpt={1}".format(
        reverse("modoboa_amavis:mail_release", args=[mail_id]), rcpt)
    delete_url = "{0}?rcpt={1}".format(
        reverse("modoboa_amavis:mail_delete", args=[mail_id]), rcpt)
    if secret_id:
        release_url += "&secret_id={0}".format(secret_id)
        delete_url += "&secret_id={0}".format(secret_id)
    entries = [
        {"name": "release",
         "img": "fa fa-check",
         "class": "btn-success",
         "url": release_url,
         "label": _("Release")},
        {"name": "delete",
         "img": "fa fa-trash",
         "class": "btn-danger",
         "url": delete_url,
         "label": _("Delete")},
    ]

    return render_to_string("common/buttons_list.html",
                            {"entries": entries})


@register.simple_tag
def quar_menu(user):
    """Render the quarantine listing menu.

    :rtype: str
    :return: resulting HTML
    """
    extraopts = [{"name": "to", "label": _("To")}]
    return render_to_string("modoboa_amavis/main_action_bar.html", {
        "extraopts": extraopts,
        "manual_learning": lib.manual_learning_enabled(user),
        "msg_types": constants.MESSAGE_TYPES
    })


@register.filter
def msgtype_to_color(msgtype):
    """Return corresponding color."""
    return constants.MESSAGE_TYPE_COLORS.get(msgtype, "default")


@register.filter
def msgtype_to_html(msgtype):
    """Transform a message type to a bootstrap label."""
    color = constants.MESSAGE_TYPE_COLORS.get(msgtype, "default")
    return mark_safe(
        "<span class=\"label label-{}\" title=\"{}\">{}</span>".format(
            color, constants.MESSAGE_TYPES[msgtype], msgtype))
