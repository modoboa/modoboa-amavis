"""Custom test runner."""

from django.apps import apps
from django.test.runner import DiscoverRunner


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"


class UnManagedModelTestRunner(DiscoverRunner):
    """
    Test runner that automatically makes all unmanaged models in your Django
    project managed for the duration of the test run.
    Many thanks to the Caktus Group: http://bit.ly/1N8TcHW
    """

    ALLOWED_MODELS = ["policy", "users"]

    def setup_test_environment(self, *args, **kwargs):
        self.unmanaged_models = []
        for m in apps.get_models():
            condition = (
                m._meta.app_label == "modoboa_amavis" and
                m._meta.model_name in self.ALLOWED_MODELS)
            if condition:
                self.unmanaged_models.append(m)
                m._meta.managed = True
        super(UnManagedModelTestRunner, self).setup_test_environment(
            *args, **kwargs)

    def teardown_test_environment(self, *args, **kwargs):
        super(UnManagedModelTestRunner, self).teardown_test_environment(
            *args, **kwargs)
        # reset unmanaged models
        for m in self.unmanaged_models:
            m._meta.managed = False
