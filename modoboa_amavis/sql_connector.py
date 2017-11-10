"""SQL connector module."""

import datetime

import chardet

from django.conf import settings
from django.db.models import Q
from django.utils.encoding import smart_bytes

from modoboa.admin.models import Domain
from modoboa.lib.db_utils import db_type

from .models import Quarantine, Msgrcpt, Maddr


def reverse_domain_names(domains):
    """Return a list of reversed domain names."""
    return [".".join(reversed(domain.split("."))) for domain in domains]


class SQLconnector(object):
    """This class handles all database operations."""

    ORDER_TRANSLATION_TABLE = {
        "type": "content",
        "score": "bspam_level",
        "date": "mail__time_num",
        "subject": "mail__subject",
        "from": "mail__from_addr",
        "to": "rid__email"
    }

    QUARANTINE_FIELDS = [
        "content",
        "bspam_level",
        "rs",
        "rid__email",
        "mail__from_addr",
        "mail__subject",
        "mail__mail_id",
        "mail__time_num",
    ]

    def __init__(self, user=None, navparams=None):
        """Constructor."""
        self.user = user
        self.navparams = navparams
        self.messages = None

        self._messages_count = None

    def _exec(self, query, args):
        """Execute a raw SQL query.

        :param string query: query to execute
        :param list args: a list of arguments to replace in :kw:`query`
        """
        from django.db import connections, transaction

        with transaction.atomic():
            cursor = connections['amavis'].cursor()
            cursor.execute(query, args)

    def _apply_msgrcpt_simpleuser_filter(self, flt):
        """Apply specific filter for simple users."""
        rcpts = [self.user.email]
        if hasattr(self.user, "mailbox"):
            rcpts += self.user.mailbox.alias_addresses
        return flt & Q(rid__email__in=rcpts)

    def _apply_msgrcpt_filters(self, flt):
        """Apply filters based on user's role."""
        if self.user.role == 'SimpleUsers':
            flt = self._apply_msgrcpt_simpleuser_filter(flt)
        elif not self.user.is_superuser:
            doms = Domain.objects.get_for_admin(
                self.user).values_list("name", flat=True)
            flt &= Q(rid__domain__in=reverse_domain_names(doms))
        return flt

    def _apply_extra_search_filter(self, crit, pattern):
        """Apply search filters using additional criterias."""
        if crit == "to":
            return Q(rid__email__contains=pattern)
        return None

    def _apply_extra_select_filters(self, messages):
        """Just a hook to apply additional filters to the queryset.

        """
        return messages

    def _get_quarantine_content(self):
        """Fetch quarantine content.

        Filters: rs, rid, content
        """
        flt = (
            Q(rs__in=[' ', 'V', 'R', 'p', 'S', 'H'])
            if self.navparams.get('viewrequests', '0') != '1' else Q(rs='p')
        )
        flt = self._apply_msgrcpt_filters(flt)
        pattern = self.navparams.get("pattern", "")
        if pattern:
            criteria = self.navparams.get('criteria')
            if criteria == "both":
                criteria = "from_addr,subject,to"
            search_flt = None
            for crit in criteria.split(","):
                if crit == "from_addr":
                    nfilter = Q(mail__from_addr__contains=pattern)
                elif crit == "subject":
                    nfilter = Q(mail__subject__contains=pattern)
                else:
                    nfilter = self._apply_extra_search_filter(crit, pattern)
                    if nfilter is None:
                        continue
                search_flt = (
                    nfilter if search_flt is None else search_flt | nfilter
                )
            if search_flt:
                flt &= search_flt
        msgtype = self.navparams.get('msgtype', None)
        if msgtype is not None:
            flt &= Q(content=msgtype)

        flt &= Q(
            mail__in=Quarantine.objects.filter(chunk_ind=1).values("mail_id")
        )
        messages = Msgrcpt.objects.select_related("mail", "rid").filter(flt)
        messages = self._apply_extra_select_filters(messages)
        return messages

    def messages_count(self):
        """Return the total number of messages living in the quarantine.

        We also store the built queryset for a later use.
        """
        if self.user is None or self.navparams is None:
            return None
        if self._messages_count is None:
            self.messages = self._get_quarantine_content()
            self.messages = self.messages.values(*self.QUARANTINE_FIELDS)

            order = self.navparams.get("order")
            if order is not None:
                sign = ""
                if order[0] == "-":
                    sign = "-"
                    order = order[1:]
                order = self.ORDER_TRANSLATION_TABLE[order]
                self.messages = self.messages.order_by(sign + order)

            self._messages_count = len(self.messages)

        return self._messages_count

    def fetch(self, start=None, stop=None):
        """Fetch a range of messages from the internal cache."""
        emails = []
        for qm in self.messages[start - 1:stop]:
            if qm["rs"] == 'D':
                continue
            m = {
                "from": qm["mail__from_addr"],
                "to": smart_bytes(qm["rid__email"]),
                "subject": qm["mail__subject"],
                "mailid": smart_bytes(qm["mail__mail_id"]),
                "date": datetime.datetime.fromtimestamp(qm["mail__time_num"]),
                "type": qm["content"],
                "score": qm["bspam_level"],
                "status": qm["rs"]
            }
            if qm["rs"] in ['', ' ']:
                m["class"] = "unseen"
            elif qm["rs"] == 'p':
                m["class"] = "pending"
            emails.append(m)
        return emails

    def get_recipient_message(self, address, mailid):
        """Retrieve a message for a given recipient.
        """
        return Msgrcpt.objects.get(
            mail=mailid, rid__email=smart_bytes(address))

    def set_msgrcpt_status(self, address, mailid, status):
        """Change the status (rs field) of a message recipient.

        :param string status: status
        """
        addr = Maddr.objects.get(email=smart_bytes(address))
        self._exec(
            "UPDATE msgrcpt SET rs=%s WHERE mail_id=%s AND rid=%s",
            [status, mailid, addr.id]
        )

    def get_domains_pending_requests(self, domains):
        """Retrieve pending release requests for a list of domains."""
        return Msgrcpt.objects.filter(
            rs='p', rid__domain__in=reverse_domain_names(domains))

    def get_pending_requests(self):
        """Return the number of requests currently pending."""
        rq = Q(rs='p')
        if not self.user.is_superuser:
            doms = Domain.objects.get_for_admin(self.user)
            if not doms.exists():
                return 0
            doms_q = Q(rid__domain__in=reverse_domain_names(
                doms.values_list("name", flat=True)))
            rq &= doms_q
        return Msgrcpt.objects.filter(rq).count()

    def get_mail_content(self, mailid):
        """Retrieve the content of a message."""
        content = b"".join([
            smart_bytes(qmail.mail_text)
            for qmail in Quarantine.objects.filter(
                    mail=smart_bytes(mailid))
        ])
        try:
            content = content.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            return content
        try:
            result = chardet.detect(content)
        except UnicodeDecodeError:
            raise
        return content.decode(result["encoding"])


class PgSQLconnector(SQLconnector):

    """
    The postgres version.

    Make use of ``QuerySet.extra`` and postgres ``convert_from``
    function to let the quarantine manager work as expected !

    The T4 alias is not a random choice. The generated query was
    dumped to found it. Be careful since it can changes with
    future Django versions...

    """

    def _apply_msgrcpt_simpleuser_filter(self, flt):
        """Return filters based on user's role. """
        self._where = []
        rcpts = [self.user.email]
        if hasattr(self.user, "mailbox"):
            rcpts += self.user.mailbox.alias_addresses
        self._where.append(
            "convert_from(maddr.email, '{}') IN ({})".format(
                settings.AMAVIS_DEFAULT_DATABASE_ENCODING,
                ','.join(["'%s'" % rcpt for rcpt in rcpts]))
        )
        return flt

    def _apply_extra_search_filter(self, crit, pattern):
        """Apply search filters using additional criterias."""
        if crit == "to":
            if not hasattr(self, "_where"):
                self._where = []
            self._where.append(
                "convert_from(maddr.email, '{}') LIKE '%%{}%%'".format(
                    settings.AMAVIS_DEFAULT_DATABASE_ENCODING, pattern)
            )
        return None

    def _apply_extra_select_filters(self, messages):
        """Just a hook to apply additional filters to the queryset."""
        if hasattr(self, "_where"):
            messages = messages.extra(where=self._where)
        return messages

    def get_recipient_message(self, address, mailid):
        """Retrieve a message for a given recipient."""
        qset = Msgrcpt.objects.filter(mail=mailid).extra(
            where=["msgrcpt.rid=maddr.id",
                   "convert_from(maddr.email, '{}') = '{}'".format(
                       settings.AMAVIS_DEFAULT_DATABASE_ENCODING, address)],
            tables=['maddr']
        )
        return qset.all()[0]


def get_connector(**kwargs):
    """Return the appropriate *connector* class.

    The result depends on the DB engine in use.
    """
    if db_type("amavis") == 'postgres':
        return PgSQLconnector(**kwargs)
    return SQLconnector(**kwargs)
