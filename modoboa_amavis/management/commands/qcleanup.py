#!/usr/bin/env python
# coding: utf-8

import time

from django.core.management.base import BaseCommand

from modoboa.parameters import tools as param_tools

from ...models import Msgrcpt, Msgs, Maddr
from ...modo_extension import Amavis


class Command(BaseCommand):
    args = ""
    help = "Amavis quarantine cleanup"

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--debug", action="store_true", default=False,
            help="Activate debug output")
        parser.add_argument(
            "--verbose", action="store_true", default=False,
            help="Display informational messages")

    def __vprint(self, msg):
        if not self.verbose:
            return
        print msg

    def handle(self, *args, **options):
        Amavis().load()
        if options["debug"]:
            import logging
            l = logging.getLogger("django.db.backends")
            l.setLevel(logging.DEBUG)
            l.addHandler(logging.StreamHandler())
        self.verbose = options["verbose"]

        conf = dict(param_tools.get_global_parameters("modoboa_amavis"))

        flags = ["D"]
        if conf["released_msgs_cleanup"]:
            flags += ["R"]

        self.__vprint("Deleting marked messages...")
        ids = Msgrcpt.objects.filter(rs__in=flags).values("mail_id").distinct()
        for msg in Msgs.objects.filter(mail_id__in=ids):
            if not msg.msgrcpt_set.exclude(rs__in=flags).count():
                msg.delete()

        self.__vprint(
            "Deleting messages older than %d days...".format(
                conf["max_messages_age"]))
        limit = int(time.time()) - (conf["max_messages_age"] * 24 * 3600)
        Msgs.objects.filter(time_num__lt=limit).delete()

        self.__vprint("Deleting unreferenced e-mail addresses...")
        for maddr in Maddr.objects.all():
            if not maddr.msgs_set.count() and not maddr.msgrcpt_set.count():
                maddr.delete()

        self.__vprint("Done.")
