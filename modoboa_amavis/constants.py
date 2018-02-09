# -*- coding: utf-8 -*-

"""Modoboa amavis constants."""

from __future__ import unicode_literals

import collections

from django.utils.translation import ugettext_lazy as _

MESSAGE_TYPES = collections.OrderedDict((
    ("C", _("Clean")),
    ("S", _("Spam")),
    ("Y", _("Spammy")),
    ("V", _("Virus")),
    ("H", _("Bad Header")),
    ("M", _("Bad MIME")),
    ("B", _("Banned")),
    ("O", _("Over sized")),
    ("T", _("MTA error")),
    ("U", _("Unchecked")),
))

MESSAGE_TYPE_COLORS = {
    "C": "success",
    "S": "danger",
    "Y": "warning",
    "V": "danger",
    "H": "warning",
    "M": "warning",
    "B": "warning",
    "O": "warning",
    "T": "warning",
    "U": "default"
}
