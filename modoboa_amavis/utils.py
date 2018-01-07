# -*- coding: utf-8 -*-

"""A collection of utility functions for working with the Amavis database."""

from __future__ import unicode_literals

from django.conf import settings
from django.db.models.expressions import Func
from django.utils import six
from django.utils.encoding import smart_bytes as django_smart_bytes
from django.utils.encoding import smart_str as django_smart_str
from django.utils.encoding import smart_text as django_smart_text


"""
Byte fields for text data are EVIL.

MySQL uses `varbyte` fields which mysqlclient client maps to `str` (Py2) or
`bytes` (Py3), Djangos smart_* functions work as expected.

PostgreSQL uses `bytea` fields which psycopg2 maps to `memoryview`,
Djangos smart_* functions don't work as expected, you must call `tobytes()` on
the memoryview for them to work.

For convenience use smart_bytes and smart_text from this file in modoboa_amavis
to avoid any headaches.
"""


def smart_bytes(value, *args, **kwargs):
    if isinstance(value, memoryview):
        value = value.tobytes()
    return django_smart_bytes(value, *args, **kwargs)


def smart_str(value, *args, **kwargs):
    if isinstance(value, memoryview):
        value = value.tobytes()
    return django_smart_str(value, *args, **kwargs)


def smart_text(value, *args, **kwargs):
    if isinstance(value, memoryview):
        value = value.tobytes()
    return django_smart_text(value, *args, **kwargs)


def fix_utf8_encoding(value):
    """Fix utf-8 strings that contain utf-8 escaped characters.

    msgs.from_addr and msgs.subject potentialy contain badly escaped utf-8
    characters, this utility function fixes that and should be used anytime
    these fields are accesses.

    Didn't even know the raw_unicode_escape encoding existed :)
    https://docs.python.org/2/library/codecs.html?highlight=raw_unicode_escape#python-specific-encodings
    https://docs.python.org/3/library/codecs.html?highlight=raw_unicode_escape#python-specific-encodings
    """
    assert isinstance(value, six.text_type), \
        ("value should be of type %s" % six.text_type.__name__)
    return value.encode("raw_unicode_escape").decode("utf-8")


class ConvertFrom(Func):
    """Convert a binary value to a string.
    Calls the database specific function to convert a binary value to a string
    using the encoding set in AMAVIS_DEFAULT_DATABASE_ENCODING.
    """

    """PostgreSQL implementation.
    See https://www.postgresql.org/docs/9.3/static/functions-string.html#FUNCTIONS-STRING-OTHER"""
    function = "convert_from"
    arity = 1
    template = "%(function)s(%(expressions)s, '{}')".format(
        settings.AMAVIS_DEFAULT_DATABASE_ENCODING)

    def as_mysql(self, compiler, connection):
        """MySQL implementation.
        See https://dev.mysql.com/doc/refman/5.5/en/cast-functions.html#function_convert"""
        return super(ConvertFrom, self).as_sql(
            compiler, connection,
            function="CONVERT",
            template="%(function)s(%(expressions)s USING {})".format(
                settings.AMAVIS_DEFAULT_DATABASE_ENCODING),
            arity=1,
        )

    def as_sqlite(self, compiler, connection):
        """SQLite implementation.
        SQLite has no equivilant function, just return the field."""
        return super(ConvertFrom, self).as_sql(
            compiler, connection,
            template="%(expressions)s",
            arity=1,
        )
