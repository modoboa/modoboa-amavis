"""Amavis factories."""

import datetime
import time

from django.utils.encoding import smart_bytes

import factory

from . import models


class MaddrFactory(factory.DjangoModelFactory):
    """Factory for Maddr."""

    class Meta:
        model = models.Maddr

    id = factory.Sequence(lambda n: n)
    email = factory.Sequence(lambda n: "user_{}@domain.test".format(n))
    domain = "test.domain"


class MsgsFactory(factory.DjangoModelFactory):
    """Factory for Mailaddr."""

    class Meta:
        model = models.Msgs

    mail_id = factory.Sequence(lambda n: smart_bytes("mailid{}".format(n)))
    partition_tag = 0
    secret_id = factory.Sequence(lambda n: smart_bytes("id{}".format(n)))
    sid = factory.SubFactory(MaddrFactory)
    client_addr = "127.0.0.1"
    originating = "Y"
    dsn_sent = "N"
    subject = factory.Sequence(lambda n: "Test message {}".format(n))
    time_num = factory.LazyAttribute(lambda o: int(time.time()))
    time_iso = factory.LazyAttribute(
        lambda o: datetime.datetime.fromtimestamp(o.time_num).isoformat())
    size = 100


class MsgrcptFactory(factory.DjangoModelFactory):
    """Factory for Msgrcpt."""

    class Meta:
        model = models.Msgrcpt

    partition_tag = 0
    rseqnum = 1
    is_local = "Y"
    bl = "N"
    wl = "N"
    mail = factory.SubFactory(MsgsFactory)
    rid = factory.SubFactory(MaddrFactory)


class QuarantineFactory(factory.DjangoModelFactory):
    """Factory for Quarantine."""

    class Meta:
        model = models.Quarantine

    partition_tag = 0
    chunk_ind = 1
    mail = factory.SubFactory(MsgsFactory)
