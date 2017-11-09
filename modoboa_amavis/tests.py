"""Amavis tests."""

from django.core.urlresolvers import reverse

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
        cls.msgrcpt = factories.MsgrcptFactory(
            bspam_level=999.0, content="S", rs=" ",
            rid__email=b"user@test.com",
            rid__domain="com.test"
        )
        cls.quarantine = factories.QuarantineFactory(
            mail=cls.msgrcpt.mail,
            mail_text=b"""X-Envelope-To: <user@test.com>
X-Envelope-To-Blocked: <user@test.com>
X-Quarantine-ID: <nq6ekd4wtXZg>
X-Spam-Flag: YES
X-Spam-Score: 1000.985
X-Spam-Level: ****************************************************************
X-Spam-Status: Yes, score=1000.985 tag=2 tag2=6.31 kill=6.31
	tests=[ALL_TRUSTED=-1, GTUBE=1000, PYZOR_CHECK=1.985]
	autolearn=no autolearn_force=no
Received: from demo.modoboa.org ([127.0.0.1])
	by localhost (demo.modoboa.org [127.0.0.1]) (amavisd-new, port 10024)
	with ESMTP id nq6ekd4wtXZg for <user@demo.local>;
	Thu,  9 Nov 2017 15:59:52 +0100 (CET)
Received: from demo.modoboa.org (localhost [127.0.0.1])
	by demo.modoboa.org (Postfix) with ESMTP
	for <user@demo.local>; Thu,  9 Nov 2017 15:59:52 +0100 (CET)
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: base64
Subject: Sample message
From: spam@example.net
To: user@demo.local
Message-ID: <151023959268.5550.5713670714483771838@demo.modoboa.org>
User-Agent: Modoboa 1.9.1
Date: Thu, 09 Nov 2017 15:59:52 +0100

This is the GTUBE, the
        Generic
        Test for
        Unsolicited
        Bulk
        Email

If your spam filter supports it, the GTUBE provides a test by which you
can verify that the filter is installed correctly and is detecting incoming
spam. You can send yourself a test mail containing the following string of
characters (in upper case and with no white spaces and line breaks):

XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X

You should send this test mail from an account outside of your network.
"""
        )


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
        url = "{}?rcpt={}".format(url, self.msgrcpt.rid.email)
        response = self.ajax_get(url)
        self.assertIn("menu", response)
        url = reverse("modoboa_amavis:mailcontent_get", args=[mail_id])
        self.assertIn(url, response["listing"])

        response = self.client.get(url)

    def test_release_msg(self):
        """Try to release a message."""
        pass
