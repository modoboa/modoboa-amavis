"""Amavis tests."""

from django.core.urlresolvers import reverse
from django.utils.encoding import smart_text

from modoboa.admin import factories as admin_factories
from modoboa.admin import models as admin_models
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoTestCase

from . import lib
from . import factories
from . import models


class TestDataMixin(object):
    """A mixin to provide test data."""

    @classmethod
    def setUpTestData(cls):
        """Create some content."""
        super(TestDataMixin, cls).setUpTestData()
        cls.msgrcpt = factories.create_spam("user@test.com")


class DomainTestCase(ModoTestCase):
    """Check that database is populated."""

    def setUp(self):
        """Initiate test context."""
        self.admin = core_models.User.objects.get(username="admin")

    def test_create_domain(self):
        """Test domain creation."""
        domain = admin_factories.DomainFactory(name="domain.test")
        name = "@{}".format(domain.name)
        policy = models.Policy.objects.get(policy_name=name)
        user = models.Users.objects.filter(policy=policy).first()
        self.assertIsNot(user, None)
        self.assertEqual(user.email, name)

        # Create a domain alias
        self.client.force_login(self.admin)
        data = {
            "name": domain.name,
            "type": "domain",
            "enabled": domain.enabled,
            "quota": domain.quota,
            "default_mailbox_quota": domain.default_mailbox_quota,
            "aliases_1": "dalias.test"
        }
        self.ajax_post(
            reverse("admin:domain_change", args=[domain.pk]), data)
        name = "@dalias.test"
        self.assertFalse(
            models.Policy.objects.filter(policy_name=name).exists())
        user = models.Users.objects.get(email=name)
        self.assertEqual(user.policy, policy)

        # Delete domain alias
        del data["aliases_1"]
        self.ajax_post(
            reverse("admin:domain_change", args=[domain.pk]), data)
        self.assertFalse(
            models.Users.objects.filter(email=name).exists())

    def test_rename_domain(self):
        """Test domain rename."""
        domain = admin_factories.DomainFactory(name="domain.test")
        domain.name = "domain1.test"
        domain.save()
        name = "@{}".format(domain.name)
        self.assertTrue(
            models.Users.objects.filter(email=name).exists())
        self.assertTrue(
            models.Policy.objects.filter(policy_name=name).exists())

    def test_delete_domain(self):
        """Test domain removal."""
        domain = admin_factories.DomainFactory(name="domain.test")
        domain.delete(None)
        name = "@{}".format(domain.name)
        self.assertFalse(
            models.Users.objects.filter(email=name).exists())
        self.assertFalse(
            models.Policy.objects.filter(policy_name=name).exists())

    def test_update_domain_policy(self):
        """Check domain policy edition."""
        self.client.force_login(self.admin)
        domain = admin_factories.DomainFactory(name="domain.test")
        url = reverse("admin:domain_change", args=[domain.pk])
        # response = self.client.get(url)
        # self.assertContains(response, "Content filter")
        custom_title = "This is SPAM!"
        data = {
            "name": domain.name,
            "type": "domain",
            "enabled": domain.enabled,
            "quota": domain.quota,
            "default_mailbox_quota": domain.default_mailbox_quota,
            "bypass_virus_checks": "Y",
            "spam_subject_tag2_act": False,
            "spam_subject_tag2": custom_title
        }
        self.ajax_post(url, data)
        name = "@{}".format(domain.name)
        policy = models.Policy.objects.get(policy_name=name)
        self.assertEqual(policy.spam_subject_tag2, custom_title)


class ManualLearningTestCase(ModoTestCase):
    """Check manual learning mode."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(ManualLearningTestCase, cls).setUpTestData()
        admin_factories.populate_database()

    def test_alias_creation(self):
        """Check alias creation."""
        self.set_global_parameter("user_level_learning", True)

        # Fake activation because we don't have test data yet for
        # amavis...
        lib.setup_manual_learning_for_mbox(
            admin_models.Mailbox.objects.get(
                address="user", domain__name="test.com"))
        lib.setup_manual_learning_for_mbox(
            admin_models.Mailbox.objects.get(
                address="admin", domain__name="test.com"))

        values = {
            "address": "alias1000@test.com",
            "recipients": "admin@test.com",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        policy = models.Policy.objects.get(
            policy_name=values["recipients"])
        user = models.Users.objects.get(email=values["address"])
        self.assertEqual(user.policy, policy)

        values = {
            "address": "user@test.com",
            "recipients": "admin@test.com",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        policy = models.Policy.objects.get(
            policy_name=values["recipients"])
        user = models.Users.objects.get(email=values["address"])
        self.assertEqual(user.policy, policy)


class ViewsTestCase(TestDataMixin, ModoTestCase):
    """Test views."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(ViewsTestCase, cls).setUpTestData()
        admin_factories.populate_database()

    def tearDown(self):
        """Restore msgrcpt state."""
        self.msgrcpt.rs = " "
        self.msgrcpt.save(update_fields=["rs"])

    def test_index(self):
        """Test index view."""
        url = reverse("modoboa_amavis:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse("modoboa_amavis:_mail_list")
        response = self.ajax_get(url)
        self.assertIn("user@test.com", response["listing"])

    def test_viewmail(self):
        """Test view_mail view."""
        mail_id = self.msgrcpt.mail.mail_id
        url = reverse("modoboa_amavis:mail_detail", args=[mail_id])
        url = "{}?rcpt={}".format(url, smart_text(self.msgrcpt.rid.email))
        response = self.ajax_get(url)
        self.assertIn("menu", response)
        url = reverse("modoboa_amavis:mailcontent_get", args=[mail_id])
        self.assertIn(url, response["listing"])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_viewmail_selfservice(self):
        """Test view_mail in self-service mode."""
        self.client.logout()

        mail_id = self.msgrcpt.mail.mail_id
        url = reverse("modoboa_amavis:mail_detail", args=[mail_id])
        url = "{}?secret_id={}".format(
            url, smart_text(self.msgrcpt.mail.secret_id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.set_global_parameter("self_service", True)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        url = "{}&rcpt={}".format(url, smart_text(self.msgrcpt.rid.email))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse("modoboa_amavis:mailcontent_get", args=[mail_id])
        url = "{}?secret_id={}".format(
            url, smart_text(self.msgrcpt.mail.secret_id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_viewheaders(self):
        """Test headers display."""
        mail_id = self.msgrcpt.mail.mail_id
        url = reverse("modoboa_amavis:headers_detail", args=[mail_id])
        response = self.client.get(url)
        self.assertContains(response, b"X-Spam-Flag: YES")

    def test_delete_msg(self):
        """Test delete view."""

        # Initiate session
        url = reverse("modoboa_amavis:_mail_list")
        response = self.ajax_get(url)

        mail_id = self.msgrcpt.mail.mail_id
        url = reverse("modoboa_amavis:mail_delete", args=[mail_id])
        data = {"rcpt": smart_text(self.msgrcpt.rid.email)}
        response = self.ajax_post(url, data)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "D")
        self.assertEqual(
            response["message"], "1 message deleted successfully")

    def test_delete_selfservice(self):
        """Test delete view in self-service mode."""
        self.client.logout()
        mail_id = self.msgrcpt.mail.mail_id
        url = reverse("modoboa_amavis:mail_delete", args=[mail_id])
        url = "{}?secret_id={}".format(
            url, smart_text(self.msgrcpt.mail.secret_id))
        self.set_global_parameter("self_service", True)
        self.ajax_get(url, status=400)
        url = "{}&rcpt={}".format(url, smart_text(self.msgrcpt.rid.email))
        self.ajax_get(url)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "D")
