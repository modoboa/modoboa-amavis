"""Amavis factories."""

import datetime
import time

from django.utils.encoding import smart_bytes

import factory

from . import models

SPAM_BODY = """X-Envelope-To: <{rcpt}>
X-Envelope-To-Blocked: <{rcpt}>
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
From: {sender}
To: {rcpt}
Message-ID: <151023959268.5550.5713670714483771838@demo.modoboa.org>
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


def create_spam(rcpt, sender="spam@evil.corp"):
    """Create a spam."""
    msgrcpt = MsgrcptFactory(
        bspam_level=999.0, content="S", rs=" ",
        rid__email=smart_bytes(rcpt),
        rid__domain="com.test",
        mail__sid__email=smart_bytes(sender),
        mail__sid__domain="",
    )
    QuarantineFactory(
        mail=msgrcpt.mail,
        mail_text=smart_bytes(SPAM_BODY.format(rcpt=rcpt, sender=sender))
    )
    return msgrcpt
