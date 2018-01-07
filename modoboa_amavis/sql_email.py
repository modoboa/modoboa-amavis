# -*- coding: utf-8 -*-

"""
An email representation based on a database record.
"""

from __future__ import unicode_literals

from django.template.loader import render_to_string

from html2text import HTML2Text

from modoboa.lib.email_utils import Email

from .sql_connector import get_connector
from .utils import smart_text


class SQLemail(Email):

    """The SQL version of the Email class."""

    def __init__(self, *args, **kwargs):
        super(SQLemail, self).__init__(*args, **kwargs)
        self.qtype = ""
        self.qreason = ""

        qreason = self.msg["X-Amavis-Alert"]
        if qreason:
            if ',' in qreason:
                self.qtype, qreason = qreason.split(',', 1)
            elif qreason.startswith("BAD HEADER SECTION "):
                # Workaround for amavis <= 2.8.0 :p
                self.qtype = "BAD HEADER SECTION"
                qreason = qreason[19:]

            qreason = " ".join([x.strip() for x in qreason.splitlines()])
            self.qreason = qreason

    def _fetch_message(self):
        return get_connector().get_mail_content(self.mailid)

    @property
    def body(self):
        if self._body is None:
            super(SQLemail, self).body

        # if there's no plain text version available attempt to make one by
        # sanitising the html version. The output isn't always pretty but it
        # is readable, better than a blank screen and helps the user decide
        # if the message is spam or ham.
        if self.dformat == "plain" and not self.contents["plain"] \
                and self.contents["html"]:
            h = HTML2Text()
            h.ignore_tables = True
            h.images_to_alt = True
            mail_text = h.handle(self.contents["html"])
            self.contents["plain"] = smart_text(mail_text)
            self._post_process_plain()
            self._body = self.viewmail_plain()

        return self._body

    def render_headers(self, **kwargs):
        context = {
            "qtype": self.qtype,
            "qreason": self.qreason,
            "headers": self.headers,
        }
        return render_to_string("modoboa_amavis/mailheaders.html", context)
