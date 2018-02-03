# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

from django.contrib.sites import models as sites_models
from django.core import mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import ugettext as _

from modoboa.admin.models import Domain
from modoboa.core.models import User
from modoboa.parameters import tools as param_tools
from ...models import Msgrcpt
from ...modo_extension import Amavis
from ...sql_connector import SQLconnector


class Command(BaseCommand):
    help = "Amavis notification tool"  # NOQA:A003

    sender = None
    baseurl = None
    listingurl = None

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--smtp_host", type=str, default="localhost",
            help="The address of the SMTP server used to send notifications")
        parser.add_argument(
            "--smtp_port", type=int, default=25,
            help=("The listening port of the SMTP server used to send "
                  "notifications"))
        parser.add_argument("--verbose", action="store_true",
                            help="Activate verbose mode")

    def handle(self, *args, **options):
        Amavis().load()
        self.options = options
        self.notify_admins_pending_requests()

    def _build_message(self, rcpt, total, reqs):
        """Build new EmailMessage instance."""
        if self.options["verbose"]:
            print("Sending notification to %s" % rcpt)
        context = {
            "total": total,
            "requests": reqs,
            "baseurl": self.baseurl,
            "listingurl": self.listingurl
        }
        content = render_to_string(
            "modoboa_amavis/notifications/pending_requests.html",
            context
        )
        msg = mail.EmailMessage(
            _("[modoboa] Pending release requests"),
            content,
            self.sender,
            [rcpt]
        )
        return msg

    def notify_admins_pending_requests(self):
        self.sender = param_tools.get_global_parameter(
            "notifications_sender", app="modoboa_amavis")
        self.baseurl = "https://{}".format(
            sites_models.Site.objects.get_current().domain)
        self.listingurl = "{}{}?viewrequests=1".format(
            self.baseurl, reverse("modoboa_amavis:_mail_list"))

        messages = []
        # Check domain administators first.
        for da in User.objects.filter(groups__name="DomainAdmins"):
            if not hasattr(da, "mailbox"):
                continue
            rcpt = da.mailbox.full_address
            reqs = SQLconnector().get_domains_pending_requests(
                Domain.objects.get_for_admin(da).values_list("name", flat=True)
            )
            total = reqs.count()
            reqs = reqs.all()[:10]
            if reqs.count():
                messages.append(self._build_message(rcpt, total, reqs))

        # Then super administators.
        reqs = Msgrcpt.objects.filter(rs="p")
        total = reqs.count()
        if total:
            reqs = reqs.all()[:10]
            for su in User.objects.filter(is_superuser=True):
                if not hasattr(su, "mailbox"):
                    continue
                rcpt = su.mailbox.full_address
                messages.append(self._build_message(rcpt, total, reqs))

        # Finally, send emails.
        if not len(messages):
            return
        kwargs = {
            "host": self.options["smtp_host"],
            "port": self.options["smtp_port"]
        }
        with mail.get_connection(**kwargs) as connection:
            connection.send_messages(messages)
