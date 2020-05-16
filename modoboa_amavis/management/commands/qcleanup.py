#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import time

from django.core.management.base import BaseCommand
from django.db.models import Count

from modoboa.parameters import tools as param_tools
from ...models import Maddr, Msgrcpt, Msgs
from ...modo_extension import Amavis


class Command(BaseCommand):
    args = ""
    help = "Amavis quarantine cleanup"  # NOQA:A003

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
        print(msg)

    def handle(self, *args, **options):
        Amavis().load()
        if options["debug"]:
            import logging
            log = logging.getLogger("django.db.backends")
            log.setLevel(logging.DEBUG)
            log.addHandler(logging.StreamHandler())
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
            "Deleting messages older than {} days...".format(
                conf["max_messages_age"]))
        limit = int(time.time()) - (conf["max_messages_age"] * 24 * 3600)
        # Delete older messages in batches.
        # This would avoid consuming too much RAM when
        # having to delete many thousands of messages
        # leading to process OOM kill or soft crash.
        res = Msgs.objects.filter(time_num__lt=limit)[:5000]
        while res.count() != 0:
            for item in res:
                item.delete()
            res = Msgs.objects.filter(time_num__lt=limit)[:5000]
        
        
        self.__vprint("Deleting unreferenced e-mail addresses...")
        # Delete unreferenced email addresses in batches.
        # This would avoid consuming too much RAM when
        # having to delete many thousands of messages
        # leading to process OOM kill or soft crash.
        res = Maddr.objects.annotate(
            msgs_count=Count("msgs"), msgrcpt_count=Count("msgrcpt")
        ).filter(msgs_count=0, msgrcpt_count=0)[:100000]
        
        while res.count() != 0:
            for item in res:
                item.delete()

            res = Maddr.objects.annotate(
                msgs_count=Count("msgs"), msgrcpt_count=Count("msgrcpt")
            ).filter(msgs_count=0, msgrcpt_count=0)[:100000]

        self.__vprint("Done.")
