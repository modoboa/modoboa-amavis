#!/usr/bin/env python
# coding: utf-8
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from modoboa.admin.models import Domain
from modoboa.core.models import User
from modoboa.lib import parameters
from modoboa.lib.email_utils import sendmail_simple

from ...models import Msgrcpt
from ...modo_extension import Amavis
from ...sql_connector import get_connector


class Command(BaseCommand):
    help = 'Amavis notification tool'

    sender = None
    baseurl = None
    listingurl = None

    option_list = BaseCommand.option_list + (
        make_option("--baseurl", type="string", default=None,
                    help="The scheme and hostname used to access Modoboa"),
        make_option("--smtp_host", type="string", default="localhost",
                    help="The address of the SMTP server used to send notifications"),
        make_option("--smtp_port", type="int", default=25,
                    help="The listening port of the SMTP server used to send notifications"),
        make_option("--verbose", action="store_true",
                    help="Activate verbose mode")
    )

    def handle(self, *args, **options):
        if options["baseurl"] is None:
            raise CommandError("You must provide the --baseurl option")
        Amavis().load()
        self.options = options
        self.notify_admins_pending_requests()

    def send_pr_notification(self, rcpt, reqs):
        if self.options["verbose"]:
            print "Sending notification to %s" % rcpt
        total = reqs.count()
        reqs = reqs.all()[:10]
        content = render_to_string(
            "modoboa_amavis/notifications/pending_requests.html", dict(
                total=total, requests=reqs,
                baseurl=self.baseurl, listingurl=self.listingurl
            )
        )
        status, msg = sendmail_simple(
            self.sender, rcpt,
            subject=_("[modoboa] Pending release requests"),
            content=content,
            server=self.options["smtp_host"],
            port=self.options["smtp_port"]
        )
        if not status:
            print msg

    def notify_admins_pending_requests(self):
        self.sender = parameters.get_admin("NOTIFICATIONS_SENDER",
                                           app="modoboa_amavis")
        self.baseurl = self.options["baseurl"].strip("/")
        self.listingurl = self.baseurl \
            + reverse("modoboa_amavis:_mail_list") \
            + "?viewrequests=1"

        for da in User.objects.filter(groups__name="DomainAdmins"):
            if not hasattr(da, "mailbox"):
                continue
            rcpt = da.mailbox.full_address
            reqs = get_connector().get_domains_pending_requests(
                Domain.objects.get_for_admin(da)
            )
            if reqs.count():
                self.send_pr_notification(rcpt, reqs)

        reqs = Msgrcpt.objects.filter(rs='p')
        if not reqs.count():
            if self.options["verbose"]:
                print "No release request currently pending"
            return
        for su in User.objects.filter(is_superuser=True):
            if not hasattr(su, "mailbox"):
                continue
            rcpt = su.mailbox.full_address
            self.send_pr_notification(rcpt, reqs)
