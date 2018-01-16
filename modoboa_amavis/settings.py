# -*- coding: utf-8 -*-

"""Amavis frontend default settings."""

from __future__ import unicode_literals


def apply(settings):
    """Modify settings."""
    if "DATABASE_ROUTERS" not in settings:
        settings["DATABASE_ROUTERS"] = []
    settings["DATABASE_ROUTERS"] += ["modoboa_amavis.dbrouter.AmavisRouter"]

    if "SILENCED_SYSTEM_CHECKS" not in settings:
        settings["SILENCED_SYSTEM_CHECKS"] = []
    settings["SILENCED_SYSTEM_CHECKS"] += ["fields.W342"]

    settings["AMAVIS_DEFAULT_DATABASE_ENCODING"] = "LATIN1"
    # settings["SA_LOOKUP_PATH"] = ("/usr/bin", )
