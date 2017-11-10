"""Amavis tests."""

import os

import mock

from django.core.urlresolvers import reverse
from django.test import override_settings
from django.utils.encoding import smart_text

from modoboa.admin import factories as admin_factories
from modoboa.lib.tests import ModoTestCase

from .. import factories


class TestDataMixin(object):
    """A mixin to provide test data."""

    @classmethod
    def setUpTestData(cls):
        """Create some content."""
        super(TestDataMixin, cls).setUpTestData()
        cls.msgrcpt = factories.create_spam("user@test.com")


@override_settings(SA_LOOKUP_PATH=(os.path.dirname(__file__), ))
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

    @mock.patch("socket.socket")
    def test_release(self, mock_socket):
        """Test release view."""

        # Initiate session
        url = reverse("modoboa_amavis:_mail_list")
        response = self.ajax_get(url)

        mock_socket.return_value.recv.return_value = b"250 1234 Ok\r\n"
        mail_id = self.msgrcpt.mail.mail_id
        url = reverse("modoboa_amavis:mail_release", args=[mail_id])
        data = {"rcpt": smart_text(self.msgrcpt.rid.email)}
        response = self.ajax_post(url, data)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "R")
        self.assertEqual(
            response["message"], "1 message released successfully")

    @mock.patch("socket.socket")
    def test_release_selfservice(self, mock_socket):
        """Test release view."""
        mock_socket.return_value.recv.return_value = b"250 1234 Ok\r\n"
        self.client.logout()
        mail_id = self.msgrcpt.mail.mail_id
        url = reverse("modoboa_amavis:mail_release", args=[mail_id])
        url = "{}?secret_id={}".format(
            url, smart_text(self.msgrcpt.mail.secret_id))
        self.set_global_parameter("self_service", True)
        self.set_global_parameter("user_can_release", True)
        self.ajax_get(url, status=400)
        url = "{}&rcpt={}".format(url, smart_text(self.msgrcpt.rid.email))
        self.ajax_get(url)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "R")

    @mock.patch("socket.socket")
    def test_process(self, mock_socket):
        """Test process mode (bulk)."""
        # Initiate session
        url = reverse("modoboa_amavis:_mail_list")
        response = self.ajax_get(url)

        msgrcpt = factories.create_spam("user@test.com")
        url = reverse("modoboa_amavis:mail_process")
        selection = [
            "{} {}".format(
                smart_text(self.msgrcpt.rid.email),
                smart_text(self.msgrcpt.mail.mail_id)),
            "{} {}".format(
                smart_text(msgrcpt.rid.email),
                smart_text(msgrcpt.mail.mail_id)),
        ]
        mock_socket.return_value.recv.side_effect = (
            b"250 1234 Ok\r\n", b"250 1234 Ok\r\n")
        data = {
            "action": "release",
            "rcpt": smart_text(self.msgrcpt.rid.email),
            "selection": ",".join(selection)
        }
        response = self.ajax_post(url, data)
        self.assertEqual(
            response["message"], "2 messages released successfully")

        data = {
            "action": "delete",
            "rcpt": smart_text(self.msgrcpt.rid.email),
            "selection": ",".join(selection)
        }
        response = self.ajax_post(url, data)
        self.assertEqual(
            response["message"], "2 messages deleted successfully")

    def _test_mark_message(self, action, status):
        """Mark message common code."""
        mail_id = self.msgrcpt.mail.mail_id
        url = reverse("modoboa_amavis:mail_mark_as_" + action, args=[mail_id])
        data = {"rcpt": smart_text(self.msgrcpt.rid.email)}
        response = self.ajax_post(url, data)
        self.assertEqual(
            response["message"], "1 message processed successfully")
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, status)

        self.msgrcpt.rs = " "
        self.msgrcpt.save(update_fields=["rs"])
        self.set_global_parameter("sa_is_local", False)
        response = self.ajax_post(url, data)
        self.assertEqual(
            response["message"], "1 message processed successfully")
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, status)

    def test_mark_as_ham(self):
        """Test mark_as_ham view."""
        self._test_mark_message("ham", "H")

    def test_mark_as_spam(self):
        """Test mark_as_spam view."""
        self._test_mark_message("spam", "S")
