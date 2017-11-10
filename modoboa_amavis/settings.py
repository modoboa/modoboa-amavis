"""Amavis frontend default settings."""

DATABASE_ROUTERS = ["modoboa_amavis.dbrouter.AmavisRouter"]

SILENCED_SYSTEM_CHECKS = ["fields.W342", ]

AMAVIS_DEFAULT_DATABASE_ENCODING = "LATIN1"

# SA_LOOKUP_PATH = ("/usr/bin", )
