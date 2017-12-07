# coding: utf-8
"""
Amavis management frontend.

Provides:

* SQL quarantine management
* Per-domain settings

"""

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy

from modoboa.admin.models import Domain
from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.parameters import tools as param_tools

from . import __version__
from .lib import create_user_and_policy, create_user_and_use_policy
from . import forms


class Amavis(ModoExtension):
    """The Amavis extension."""

    name = "modoboa_amavis"
    label = ugettext_lazy("Amavis frontend")
    version = __version__
    description = ugettext_lazy("Simple amavis management frontend")
    url = "quarantine"
    available_for_topredirection = True

    def load(self):
        param_tools.registry.add("global", forms.ParametersForm, "Amavis")
        param_tools.registry.add(
            "user", forms.UserSettings, ugettext_lazy("Quarantine"))

    def load_initial_data(self):
        """Create records for existing domains and co."""
        for dom in Domain.objects.all():
            policy = create_user_and_policy("@{0}".format(dom.name))
            for domalias in dom.domainalias_set.all():
                domalias_pattern = "@{0}".format(domalias.name)
                create_user_and_use_policy(domalias_pattern, policy)


exts_pool.register_extension(Amavis)
