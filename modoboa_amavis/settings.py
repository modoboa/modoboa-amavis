"""Amavis frontend default settings."""

DATABASE_ROUTERS = ["modoboa_amavis.dbrouter.AmavisRouter"]

SILENCED_SYSTEM_CHECKS = ["fields.W342", ]
