# -*- coding: utf-8 -*-

"""Tests for sql_email."""

from __future__ import unicode_literals

import os

from django.test import TestCase
from django.utils.encoding import smart_bytes, smart_text

from ..sql_email import SQLemail

SAMPLES_DIR = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "sample_messages"))


class EmailTestImplementation(SQLemail):

    def _fetch_message(self):
        message_path = os.path.join(SAMPLES_DIR, "%s-input.txt" % self.mailid)
        assert os.path.isfile(message_path), "%s does not exist." % message_path

        with open(message_path, "rb") as fp:
            mail_text = smart_bytes(fp.read())

        return mail_text


class EmailTests(TestCase):
    """Tests for modoboa_amavis.sql_email.SQLEmail

    When writing new sample messages use the following naming convention for
    the sample files stored in sample_messages:

    input:  {message_id}-input.txt
    output: {message_id}-output-{dformat}_{no,}links.txt
    """

    def _get_expected_output(self, message_id, **kwargs):
        ext = kwargs["dformat"] if "dformat" in kwargs else "plain"
        ext += "_links" if "links" in kwargs and kwargs["links"] else "_nolinks"
        message_path = os.path.join(SAMPLES_DIR,
                                    "%s-output-%s.txt" % (message_id, ext))
        assert os.path.isfile(message_path), "%s does not exist." % message_path

        with open(message_path, "rb") as fp:
            # output should always be unicode (py2) or str (py3)
            mail_text = smart_text(fp.read())

        return mail_text

    def _test_email(self, message_id, **kwargs):
        """Boiler plate code for testing e-mails."""
        expected_output = self._get_expected_output(message_id, **kwargs)
        output = EmailTestImplementation(message_id, **kwargs).body
        self.assertEqual(output, expected_output)

    def test_amavis_aleart_header(self):
        email = EmailTestImplementation("quarantined")
        self.assertEqual(email.qtype, "BAD HEADER SECTION")
        self.assertEqual(email.qreason,
                         "Non-encoded non-ASCII data (and not UTF-8) (char 85 "
                         "hex): Subject: I think I saw you in my dreams\\x{85}")

    def test_email_multipart_with_no_text(self):
        """for a multipart message without a text/plain part convert the
           text/html to text/plain"""
        self._test_email("quarantined")
