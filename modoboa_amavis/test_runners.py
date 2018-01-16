# -*- coding: utf-8 -*-

"""Custom test runner."""

from __future__ import unicode_literals

from django.apps import apps
from django.test.runner import DiscoverRunner


class UnManagedModelTestRunner(DiscoverRunner):
    """
    Test runner that automatically makes all unmanaged models in your Django
    project managed for the duration of the test run.
    Many thanks to the Caktus Group: http://bit.ly/1N8TcHW
    """

    unmanaged_models = []

    def setup_test_environment(self, *args, **kwargs):
        """Mark modoboa_amavis models as managed during testing
        During database setup migrations are only run for managed models"""
        for m in apps.get_models():
            if m._meta.app_label == "modoboa_amavis":
                self.unmanaged_models.append(m)
                m._meta.managed = True
        super(UnManagedModelTestRunner, self).setup_test_environment(
            *args, **kwargs)

    def teardown_test_environment(self, *args, **kwargs):
        """Revert modoboa_amavis models to unmanaged"""
        super(UnManagedModelTestRunner, self).teardown_test_environment(
            *args, **kwargs)
        for m in self.unmanaged_models:
            m._meta.managed = False
