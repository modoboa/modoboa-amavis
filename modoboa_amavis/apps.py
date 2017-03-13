"""AppConfig for amavis."""

from django.apps import AppConfig


class AmavisConfig(AppConfig):
    """App configuration."""

    name = "modoboa_amavis"
    verbose_name = "Modoboa amavis frontend"

    def ready(self):
        from . import handlers
