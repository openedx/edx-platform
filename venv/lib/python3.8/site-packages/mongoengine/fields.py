import datetime
import decimal
import inspect
import itertools
import re
import socket
import time
import uuid
from io import BytesIO
from operator import itemgetter

import gridfs
import pymongo
from bson import SON, Binary, DBRef, ObjectId
from bson.int64 import Int64
from pymongo import ReturnDocument

try:
    import dateutil
except ImportError:
    dateutil = None
else:
    import dateutil.parser

from mongoengine.base import (
    BaseDocument,
    BaseField,
    ComplexBaseField,
    GeoJsonBaseField,
    LazyReference,
    ObjectIdField,
    get_document,
)
from mongoengine.base.utils import LazyRegexCompiler
from mongoengine.common import _import_class
from mongoengine.connection import DEFAULT_CONNECTION_NAME, get_db
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.errors import (
    DoesNotExist,
    InvalidQueryError,
    ValidationError,
)
from mongoengine.queryset import DO_NOTHING
from mongoengine.queryset.base import BaseQuerySet
from mongoengine.queryset.transform import STRING_OPERATORS

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None


__all__ = (
    "StringField",
    "URLField",
    "EmailField",
    "IntField",
    "LongField",
    "FloatField",
    "DecimalField",
    "BooleanField",
    "DateTimeField",
    "DateField",
    "ComplexDateTimeField",
    "EmbeddedDocumentField",
    "ObjectIdField",
    "GenericEmbeddedDocumentField",
    "DynamicField",
    "ListField",
    "SortedListField",
    "EmbeddedDocumentListField",
    "DictField",
    "MapField",
    "ReferenceField",
    "CachedReferenceField",
    "LazyReferenceField",
    "GenericLazyReferenceField",
    "GenericReferenceField",
    "BinaryField",
    "GridFSError",
    "GridFSProxy",
    "FileField",
    "ImageGridFsProxy",
    "ImproperlyConfigured",
    "ImageField",
    "GeoPointField",
    "PointField",
    "LineStringField",
    "PolygonField",
    "SequenceField",
    "UUIDField",
    "EnumField",
    "MultiPointField",
    "MultiLineStringField",
    "MultiPolygonField",
    "GeoJsonBaseField",
)

RECURSIVE_REFERENCE_CONSTANT = "self"


class StringField(BaseField):
    """A unicode string field."""

    def __init__(self, regex=None, max_length=None, min_length=None, **kwargs):
        """
        :param regex: (optional) A string pattern that will be applied during validation
        :param max_length: (optional) A max length that will be applied during validation
        :param min_length: (optional) A min length that will be applied during validation
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.BaseField`
        """
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length
        super().__init__(**kwargs)

    def to_python(self, value):
        if isinstance(value, str):
            return value
        try:
            value = value.decode("utf-8")
        except Exception:
            pass
        return value

    def validate(self, value):
        if not isinstance(value, str):
            self.error("StringField only accepts string values")

        if self.max_length is not None and len(value) > self.max_length:
            self.error("String value is too long")

        if self.min_length is not None and len(value) < self.min_length:
            self.error("String value is too short")

        if self.regex is not None and self.regex.match(value) is None:
            self.error("String value did not match validation regex")

    def lookup_member(self, member_name):
        return None

    def prepare_query_value(self, op, value):
        if not isinstance(op, str):
            return value

        if op in STRING_OPERATORS:
            case_insensitive = op.startswith("i")
            op = op.lstrip("i")

            flags = re.IGNORECASE if case_insensitive else 0

            regex = r"%s"
            if op == "startswith":
                regex = r"^%s"
            elif op == "endswith":
                regex = r"%s$"
            elif op == "exact":
                regex = r"^%s$"
            elif op == "wholeword":
                regex = r"\b%s\b"
            elif op == "regex":
                regex = value

            if op == "regex":
                value = re.compile(regex, flags)
            else:
                # escape unsafe characters which could lead to a re.error
                value = re.escape(value)
                value = re.compile(regex % value, flags)
        return super().prepare_query_value(op, value)


class URLField(StringField):
    """A field that validates input as an URL."""

    _URL_REGEX = LazyRegexCompiler(
        r"^(?:[a-z0-9\.\-]*)://"  # scheme is validated separately
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-_]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}(?<!-)\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # ...or ipv4
        r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"  # ...or ipv6
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    _URL_SCHEMES = ["http", "https", "ftp", "ftps"]

    def __init__(self, url_regex=None, schemes=None, **kwargs):
        """
        :param url_regex: (optional) Overwrite the default regex used for validation
        :param schemes: (optional) Overwrite the default URL schemes that are allowed
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.StringField`
        """
        self.url_regex = url_regex or self._URL_REGEX
        self.schemes = schemes or self._URL_SCHEMES
        super().__init__(**kwargs)

    def validate(self, value):
        # Check first if the scheme is valid
        scheme = value.split("://")[0].lower()
        if scheme not in self.schemes:
            self.error(f"Invalid scheme {scheme} in URL: {value}")

        # Then check full URL
        if not self.url_regex.match(value):
            self.error(f"Invalid URL: {value}")


class EmailField(StringField):
    """A field that validates input as an email address."""

    USER_REGEX = LazyRegexCompiler(
        # `dot-atom` defined in RFC 5322 Section 3.2.3.
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z"
        # `quoted-string` defined in RFC 5322 Section 3.2.4.
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)',
        re.IGNORECASE,
    )

    UTF8_USER_REGEX = LazyRegexCompiler(
        (
            # RFC 6531 Section 3.3 extends `atext` (used by dot-atom) to
            # include `UTF8-non-ascii`.
            r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z\u0080-\U0010FFFF]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z\u0080-\U0010FFFF]+)*\Z"
            # `quoted-string`
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)'
        ),
        re.IGNORECASE | re.UNICODE,
    )

    DOMAIN_REGEX = LazyRegexCompiler(
        r"((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))\Z",
        re.IGNORECASE,
    )

    error_msg = "Invalid email address: %s"

    def __init__(
        self,
        domain_whitelist=None,
        allow_utf8_user=False,
        allow_ip_domain=False,
        *args,
        **kwargs,
    ):
        """
        :param domain_whitelist: (optional) list of valid domain names applied during validation
        :param allow_utf8_user: Allow user part of the email to contain utf8 char
        :param allow_ip_domain: Allow domain part of the email to be an IPv4 or IPv6 address
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.StringField`
        """
        self.domain_whitelist = domain_whitelist or []
        self.allow_utf8_user = allow_utf8_user
        self.allow_ip_domain = allow_ip_domain
        super().__init__(*args, **kwargs)

    def validate_user_part(self, user_part):
        """Validate the user part of the email address. Return True if
        valid and False otherwise.
        """
        if self.allow_utf8_user:
            return self.UTF8_USER_REGEX.match(user_part)
        return self.USER_REGEX.match(user_part)

    def validate_domain_part(self, domain_part):
        """Validate the domain part of the email address. Return True if
        valid and False otherwise.
        """
        # Skip domain validation if it's in the whitelist.
        if domain_part in self.domain_whitelist:
            return True

        if self.DOMAIN_REGEX.match(domain_part):
            return True

        # Validate IPv4/IPv6, e.g. user@[192.168.0.1]
        if self.allow_ip_domain and domain_part[0] == "[" and domain_part[-1] == "]":
            for addr_family in (socket.AF_INET, socket.AF_INET6):
                try:
                    socket.inet_pton(addr_family, domain_part[1:-1])
                    return True
                except (OSError, UnicodeEncodeError):
                    pass

        return False

    def validate(self, value):
        super().validate(value)

        if "@" not in value:
            self.error(self.error_msg % value)

        user_part, domain_part = value.rsplit("@", 1)

        # Validate the user part.
        if not self.validate_user_part(user_part):
            self.error(self.error_msg % value)

        # Validate the domain and, if invalid, see if it's IDN-encoded.
        if not self.validate_domain_part(domain_part):
            try:
                domain_part = domain_part.encode("idna").decode("ascii")
            except UnicodeError:
                self.error(
                    "{} {}".format(
                        self.error_msg % value, "(domain failed IDN encoding)"
                    )
                )
            else:
                if not self.validate_domain_part(domain_part):
                    self.error(
                        "{} {}".format(
                            self.error_msg % value, "(domain validation failed)"
                        )
                    )


class IntField(BaseField):
    """32-bit integer field."""

    def __init__(self, min_value=None, max_value=None, **kwargs):
        """
        :param min_value: (optional) A min value that will be applied during validation
        :param max_value: (optional) A max value that will be applied during validation
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.BaseField`
        """
        self.min_value, self.max_value = min_value, max_value
        super().__init__(**kwargs)

    def to_python(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            pass
        return value

    def validate(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            self.error("%s could not be converted to int" % value)

        if self.min_value is not None and value < self.min_value:
            self.error("Integer value is too small")

        if self.max_value is not None and value > self.max_value:
            self.error("Integer value is too large")

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return super().prepare_query_value(op, int(value))


class LongField(BaseField):
    """64-bit integer field. (Equivalent to IntField since the support to Python2 was dropped)"""

    def __init__(self, min_value=None, max_value=None, **kwargs):
        """
        :param min_value: (optional) A min value that will be applied during validation
        :param max_value: (optional) A max value that will be applied during validation
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.BaseField`
        """
        self.min_value, self.max_value = min_value, max_value
        super().__init__(**kwargs)

    def to_python(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            pass
        return value

    def to_mongo(self, value):
        return Int64(value)

    def validate(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            self.error("%s could not be converted to long" % value)

        if self.min_value is not None and value < self.min_value:
            self.error("Long value is too small")

        if self.max_value is not None and value > self.max_value:
            self.error("Long value is too large")

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return super().prepare_query_value(op, int(value))


class FloatField(BaseField):
    """Floating point number field."""

    def __init__(self, min_value=None, max_value=None, **kwargs):
        """
        :param min_value: (optional) A min value that will be applied during validation
        :param max_value: (optional) A max value that will be applied during validation
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.BaseField`
        """
        self.min_value, self.max_value = min_value, max_value
        super().__init__(**kwargs)

    def to_python(self, value):
        try:
            value = float(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        if isinstance(value, int):
            try:
                value = float(value)
            except OverflowError:
                self.error("The value is too large to be converted to float")

        if not isinstance(value, float):
            self.error("FloatField only accepts float and integer values")

        if self.min_value is not None and value < self.min_value:
            self.error("Float value is too small")

        if self.max_value is not None and value > self.max_value:
            self.error("Float value is too large")

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return super().prepare_query_value(op, float(value))


class DecimalField(BaseField):
    """Fixed-point decimal number field. Stores the value as a float by default unless `force_string` is used.
    If using floats, beware of Decimal to float conversion (potential precision loss)
    """

    def __init__(
        self,
        min_value=None,
        max_value=None,
        force_string=False,
        precision=2,
        rounding=decimal.ROUND_HALF_UP,
        **kwargs,
    ):
        """
        :param min_value: (optional) A min value that will be applied during validation
        :param max_value: (optional) A max value that will be applied during validation
        :param force_string: Store the value as a string (instead of a float).
         Be aware that this affects query sorting and operation like lte, gte (as string comparison is applied)
         and some query operator won't work (e.g. inc, dec)
        :param precision: Number of decimal places to store.
        :param rounding: The rounding rule from the python decimal library:

            - decimal.ROUND_CEILING (towards Infinity)
            - decimal.ROUND_DOWN (towards zero)
            - decimal.ROUND_FLOOR (towards -Infinity)
            - decimal.ROUND_HALF_DOWN (to nearest with ties going towards zero)
            - decimal.ROUND_HALF_EVEN (to nearest with ties going to nearest even integer)
            - decimal.ROUND_HALF_UP (to nearest with ties going away from zero)
            - decimal.ROUND_UP (away from zero)
            - decimal.ROUND_05UP (away from zero if last digit after rounding towards zero would have been 0 or 5; otherwise towards zero)

            Defaults to: ``decimal.ROUND_HALF_UP``
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.BaseField`
        """
        self.min_value = min_value
        self.max_value = max_value
        self.force_string = force_string

        if precision < 0 or not isinstance(precision, int):
            self.error("precision must be a positive integer")

        self.precision = precision
        self.rounding = rounding

        super().__init__(**kwargs)

    def to_python(self, value):
        if value is None:
            return value

        # Convert to string for python 2.6 before casting to Decimal
        try:
            value = decimal.Decimal("%s" % value)
        except (TypeError, ValueError, decimal.InvalidOperation):
            return value
        if self.precision > 0:
            return value.quantize(
                decimal.Decimal(".%s" % ("0" * self.precision)), rounding=self.rounding
            )
        else:
            return value.quantize(decimal.Decimal(), rounding=self.rounding)

    def to_mongo(self, value):
        if value is None:
            return value
        if self.force_string:
            return str(self.to_python(value))
        return float(self.to_python(value))

    def validate(self, value):
        if not isinstance(value, decimal.Decimal):
            if not isinstance(value, str):
                value = str(value)
            try:
                value = decimal.Decimal(value)
            except (TypeError, ValueError, decimal.InvalidOperation) as exc:
                self.error("Could not convert value to decimal: %s" % exc)

        if self.min_value is not None and value < self.min_value:
            self.error("Decimal value is too small")

        if self.max_value is not None and value > self.max_value:
            self.error("Decimal value is too large")

    def prepare_query_value(self, op, value):
        return super().prepare_query_value(op, self.to_mongo(value))


class BooleanField(BaseField):
    """Boolean field type."""

    def to_python(self, value):
        try:
            value = bool(value)
        except (ValueError, TypeError):
            pass
        return value

    def validate(self, value):
        if not isinstance(value, bool):
            self.error("BooleanField only accepts boolean values")


class DateTimeField(BaseField):
    """Datetime field.

    Uses the python-dateutil library if available alternatively use time.strptime
    to parse the dates.  Note: python-dateutil's parser is fully featured and when
    installed you can utilise it to convert varying types of date formats into valid
    python datetime objects.

    Note: To default the field to the current datetime, use: DateTimeField(default=datetime.utcnow)

    Note: Microseconds are rounded to the nearest millisecond.
      Pre UTC microsecond support is effectively broken.
      Use :class:`~mongoengine.fields.ComplexDateTimeField` if you
      need accurate microsecond support.
    """

    def validate(self, value):
        new_value = self.to_mongo(value)
        if not isinstance(new_value, (datetime.datetime, datetime.date)):
            self.error('cannot parse date "%s"' % value)

    def to_mongo(self, value):
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)
        if callable(value):
            return value()

        if isinstance(value, str):
            return self._parse_datetime(value)
        else:
            return None

    @staticmethod
    def _parse_datetime(value):
        # Attempt to parse a datetime from a string
        value = value.strip()
        if not value:
            return None

        if dateutil:
            try:
                return dateutil.parser.parse(value)
            except (TypeError, ValueError, OverflowError):
                return None

        # split usecs, because they are not recognized by strptime.
        if "." in value:
            try:
                value, usecs = value.split(".")
                usecs = int(usecs)
            except ValueError:
                return None
        else:
            usecs = 0
        kwargs = {"microsecond": usecs}
        try:  # Seconds are optional, so try converting seconds first.
            return datetime.datetime(
                *time.strptime(value, "%Y-%m-%d %H:%M:%S")[:6], **kwargs
            )
        except ValueError:
            try:  # Try without seconds.
                return datetime.datetime(
                    *time.strptime(value, "%Y-%m-%d %H:%M")[:5], **kwargs
                )
            except ValueError:  # Try without hour/minutes/seconds.
                try:
                    return datetime.datetime(
                        *time.strptime(value, "%Y-%m-%d")[:3], **kwargs
                    )
                except ValueError:
                    return None

    def prepare_query_value(self, op, value):
        return super().prepare_query_value(op, self.to_mongo(value))


class DateField(DateTimeField):
    def to_mongo(self, value):
        value = super().to_mongo(value)
        # drop hours, minutes, seconds
        if isinstance(value, datetime.datetime):
            value = datetime.datetime(value.year, value.month, value.day)
        return value

    def to_python(self, value):
        value = super().to_python(value)
        # convert datetime to date
        if isinstance(value, datetime.datetime):
            value = datetime.date(value.year, value.month, value.day)
        return value


class ComplexDateTimeField(StringField):
    """
    ComplexDateTimeField handles microseconds exactly instead of rounding
    like DateTimeField does.

    Derives from a StringField so you can do `gte` and `lte` filtering by
    using lexicographical comparison when filtering / sorting strings.

    The stored string has the following format:

        YYYY,MM,DD,HH,MM,SS,NNNNNN

    Where NNNNNN is the number of microseconds of the represented `datetime`.
    The `,` as the separator can be easily modified by passing the `separator`
    keyword when initializing the field.

    Note: To default the field to the current datetime, use: DateTimeField(default=datetime.utcnow)
    """

    def __init__(self, separator=",", **kwargs):
        """
        :param separator: Allows to customize the separator used for storage (default ``,``)
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.StringField`
        """
        self.separator = separator
        self.format = separator.join(["%Y", "%m", "%d", "%H", "%M", "%S", "%f"])
        super().__init__(**kwargs)

    def _convert_from_datetime(self, val):
        """
        Convert a `datetime` object to a string representation (which will be
        stored in MongoDB). This is the reverse function of
        `_convert_from_string`.

        >>> a = datetime(2011, 6, 8, 20, 26, 24, 92284)
        >>> ComplexDateTimeField()._convert_from_datetime(a)
        '2011,06,08,20,26,24,092284'
        """
        return val.strftime(self.format)

    def _convert_from_string(self, data):
        """
        Convert a string representation to a `datetime` object (the object you
        will manipulate). This is the reverse function of
        `_convert_from_datetime`.

        >>> a = '2011,06,08,20,26,24,092284'
        >>> ComplexDateTimeField()._convert_from_string(a)
        datetime.datetime(2011, 6, 8, 20, 26, 24, 92284)
        """
        values = [int(d) for d in data.split(self.separator)]
        return datetime.datetime(*values)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        data = super().__get__(instance, owner)

        if isinstance(data, datetime.datetime) or data is None:
            return data
        return self._convert_from_string(data)

    def __set__(self, instance, value):
        super().__set__(instance, value)
        value = instance._data[self.name]
        if value is not None:
            if isinstance(value, datetime.datetime):
                instance._data[self.name] = self._convert_from_datetime(value)
            else:
                instance._data[self.name] = value

    def validate(self, value):
        value = self.to_python(value)
        if not isinstance(value, datetime.datetime):
            self.error("Only datetime objects may used in a ComplexDateTimeField")

    def to_python(self, value):
        original_value = value
        try:
            return self._convert_from_string(value)
        except Exception:
            return original_value

    def to_mongo(self, value):
        value = self.to_python(value)
        return self._convert_from_datetime(value)

    def prepare_query_value(self, op, value):
        return super().prepare_query_value(op, self._convert_from_datetime(value))


class EmbeddedDocumentField(BaseField):
    """An embedded document field - with a declared document_type.
    Only valid values are subclasses of :class:`~mongoengine.EmbeddedDocument`.
    """

    def __init__(self, document_type, **kwargs):
        # XXX ValidationError raised outside of the "validate" method.
        if not (
            isinstance(document_type, str)
            or issubclass(document_type, EmbeddedDocument)
        ):
            self.error(
                "Invalid embedded document class provided to an "
                "EmbeddedDocumentField"
            )

        self.document_type_obj = document_type
        super().__init__(**kwargs)

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, str):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                resolved_document_type = self.owner_document
            else:
                resolved_document_type = get_document(self.document_type_obj)

            if not issubclass(resolved_document_type, EmbeddedDocument):
                # Due to the late resolution of the document_type
                # There is a chance that it won't be an EmbeddedDocument (#1661)
                self.error(
                    "Invalid embedded document class provided to an "
                    "EmbeddedDocumentField"
                )
            self.document_type_obj = resolved_document_type

        return self.document_type_obj

    def to_python(self, value):
        if not isinstance(value, self.document_type):
            return self.document_type._from_son(
                value, _auto_dereference=self._auto_dereference
            )
        return value

    def to_mongo(self, value, use_db_field=True, fields=None):
        if not isinstance(value, self.document_type):
            return value
        return self.document_type.to_mongo(value, use_db_field, fields)

    def validate(self, value, clean=True):
        """Make sure that the document instance is an instance of the
        EmbeddedDocument subclass provided when the document was defined.
        """
        # Using isinstance also works for subclasses of self.document
        if not isinstance(value, self.document_type):
            self.error(
                "Invalid embedded document instance provided to an "
                "EmbeddedDocumentField"
            )
        self.document_type.validate(value, clean)

    def lookup_member(self, member_name):
        doc_and_subclasses = [self.document_type] + self.document_type.__subclasses__()
        for doc_type in doc_and_subclasses:
            field = doc_type._fields.get(member_name)
            if field:
                return field

    def prepare_query_value(self, op, value):
        if value is not None and not isinstance(value, self.document_type):
            # Short circuit for special operators, returning them as is
            if isinstance(value, dict) and all(k.startswith("$") for k in value.keys()):
                return value
            try:
                value = self.document_type._from_son(value)
            except ValueError:
                raise InvalidQueryError(
                    "Querying the embedded document '%s' failed, due to an invalid query value"
                    % (self.document_type._class_name,)
                )
        super().prepare_query_value(op, value)
        return self.to_mongo(value)


class GenericEmbeddedDocumentField(BaseField):
    """A generic embedded document field - allows any
    :class:`~mongoengine.EmbeddedDocument` to be stored.

    Only valid values are subclasses of :class:`~mongoengine.EmbeddedDocument`.

    .. note ::
        You can use the choices param to limit the acceptable
        EmbeddedDocument types
    """

    def prepare_query_value(self, op, value):
        return super().prepare_query_value(op, self.to_mongo(value))

    def to_python(self, value):
        if isinstance(value, dict):
            doc_cls = get_document(value["_cls"])
            value = doc_cls._from_son(value)

        return value

    def validate(self, value, clean=True):
        if self.choices and isinstance(value, SON):
            for choice in self.choices:
                if value["_cls"] == choice._class_name:
                    return True

        if not isinstance(value, EmbeddedDocument):
            self.error(
                "Invalid embedded document instance provided to an "
                "GenericEmbeddedDocumentField"
            )

        value.validate(clean=clean)

    def lookup_member(self, member_name):
        document_choices = self.choices or []
        for document_choice in document_choices:
            doc_and_subclasses = [document_choice] + document_choice.__subclasses__()
            for doc_type in doc_and_subclasses:
                field = doc_type._fields.get(member_name)
                if field:
                    return field

    def to_mongo(self, document, use_db_field=True, fields=None):
        if document is None:
            return None
        data = document.to_mongo(use_db_field, fields)
        if "_cls" not in data:
            data["_cls"] = document._class_name
        return data


class DynamicField(BaseField):
    """A truly dynamic field type capable of handling different and varying
    types of data.

    Used by :class:`~mongoengine.DynamicDocument` to handle dynamic data"""

    def to_mongo(self, value, use_db_field=True, fields=None):
        """Convert a Python type to a MongoDB compatible type."""

        if isinstance(value, str):
            return value

        if hasattr(value, "to_mongo"):
            cls = value.__class__
            val = value.to_mongo(use_db_field, fields)
            # If we its a document thats not inherited add _cls
            if isinstance(value, Document):
                val = {"_ref": value.to_dbref(), "_cls": cls.__name__}
            if isinstance(value, EmbeddedDocument):
                val["_cls"] = cls.__name__
            return val

        if not isinstance(value, (dict, list, tuple)):
            return value

        is_list = False
        if not hasattr(value, "items"):
            is_list = True
            value = {k: v for k, v in enumerate(value)}

        data = {}
        for k, v in value.items():
            data[k] = self.to_mongo(v, use_db_field, fields)

        value = data
        if is_list:  # Convert back to a list
            value = [v for k, v in sorted(data.items(), key=itemgetter(0))]
        return value

    def to_python(self, value):
        if isinstance(value, dict) and "_cls" in value:
            doc_cls = get_document(value["_cls"])
            if "_ref" in value:
                value = doc_cls._get_db().dereference(value["_ref"])
            return doc_cls._from_son(value)

        return super().to_python(value)

    def lookup_member(self, member_name):
        return member_name

    def prepare_query_value(self, op, value):
        if isinstance(value, str):
            return StringField().prepare_query_value(op, value)
        return super().prepare_query_value(op, self.to_mongo(value))

    def validate(self, value, clean=True):
        if hasattr(value, "validate"):
            value.validate(clean=clean)


class ListField(ComplexBaseField):
    """A list field that wraps a standard field, allowing multiple instances
    of the field to be used as a list in the database.

    If using with ReferenceFields see: :ref:`many-to-many-with-listfields`

    .. note::
        Required means it cannot be empty - as the default for ListFields is []
    """

    def __init__(self, field=None, max_length=None, **kwargs):
        self.max_length = max_length
        kwargs.setdefault("default", lambda: [])
        super().__init__(field=field, **kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            # Document class being used rather than a document object
            return self
        value = instance._data.get(self.name)
        LazyReferenceField = _import_class("LazyReferenceField")
        GenericLazyReferenceField = _import_class("GenericLazyReferenceField")
        if (
            isinstance(self.field, (LazyReferenceField, GenericLazyReferenceField))
            and value
        ):
            instance._data[self.name] = [self.field.build_lazyref(x) for x in value]
        return super().__get__(instance, owner)

    def validate(self, value):
        """Make sure that a list of valid fields is being used."""
        if not isinstance(value, (list, tuple, BaseQuerySet)):
            self.error("Only lists and tuples may be used in a list field")

        # Validate that max_length is not exceeded.
        # NOTE It's still possible to bypass this enforcement by using $push.
        # However, if the document is reloaded after $push and then re-saved,
        # the validation error will be raised.
        if self.max_length is not None and len(value) > self.max_length:
            self.error("List is too long")

        super().validate(value)

    def prepare_query_value(self, op, value):
        # Validate that the `set` operator doesn't contain more items than `max_length`.
        if op == "set" and self.max_length is not None and len(value) > self.max_length:
            self.error("List is too long")

        if self.field:

            # If the value is iterable and it's not a string nor a
            # BaseDocument, call prepare_query_value for each of its items.
            if (
                op in ("set", "unset", None)
                and hasattr(value, "__iter__")
                and not isinstance(value, str)
                and not isinstance(value, BaseDocument)
            ):
                return [self.field.prepare_query_value(op, v) for v in value]

            return self.field.prepare_query_value(op, value)

        return super().prepare_query_value(op, value)


class EmbeddedDocumentListField(ListField):
    """A :class:`~mongoengine.ListField` designed specially to hold a list of
    embedded documents to provide additional query helpers.

    .. note::
        The only valid list values are subclasses of
        :class:`~mongoengine.EmbeddedDocument`.
    """

    def __init__(self, document_type, **kwargs):
        """
        :param document_type: The type of
         :class:`~mongoengine.EmbeddedDocument` the list will hold.
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.ListField`
        """
        super().__init__(field=EmbeddedDocumentField(document_type), **kwargs)


class SortedListField(ListField):
    """A ListField that sorts the contents of its list before writing to
    the database in order to ensure that a sorted list is always
    retrieved.

    .. warning::
        There is a potential race condition when handling lists.  If you set /
        save the whole list then other processes trying to save the whole list
        as well could overwrite changes.  The safest way to append to a list is
        to perform a push operation.
    """

    def __init__(self, field, **kwargs):
        self._ordering = kwargs.pop("ordering", None)
        self._order_reverse = kwargs.pop("reverse", False)
        super().__init__(field, **kwargs)

    def to_mongo(self, value, use_db_field=True, fields=None):
        value = super().to_mongo(value, use_db_field, fields)
        if self._ordering is not None:
            return sorted(
                value, key=itemgetter(self._ordering), reverse=self._order_reverse
            )
        return sorted(value, reverse=self._order_reverse)


def key_not_string(d):
    """Helper function to recursively determine if any key in a
    dictionary is not a string.
    """
    for k, v in d.items():
        if not isinstance(k, str) or (isinstance(v, dict) and key_not_string(v)):
            return True


def key_starts_with_dollar(d):
    """Helper function to recursively determine if any key in a
    dictionary starts with a dollar
    """
    for k, v in d.items():
        if (k.startswith("$")) or (isinstance(v, dict) and key_starts_with_dollar(v)):
            return True


class DictField(ComplexBaseField):
    """A dictionary field that wraps a standard Python dictionary. This is
    similar to an embedded document, but the structure is not defined.

    .. note::
        Required means it cannot be empty - as the default for DictFields is {}
    """

    def __init__(self, field=None, *args, **kwargs):
        self._auto_dereference = False

        kwargs.setdefault("default", lambda: {})
        super().__init__(*args, field=field, **kwargs)

    def validate(self, value):
        """Make sure that a list of valid fields is being used."""
        if not isinstance(value, dict):
            self.error("Only dictionaries may be used in a DictField")

        if key_not_string(value):
            msg = "Invalid dictionary key - documents must have only string keys"
            self.error(msg)

        # Following condition applies to MongoDB >= 3.6
        # older Mongo has stricter constraints but
        # it will be rejected upon insertion anyway
        # Having a validation that depends on the MongoDB version
        # is not straightforward as the field isn't aware of the connected Mongo
        if key_starts_with_dollar(value):
            self.error(
                'Invalid dictionary key name - keys may not startswith "$" characters'
            )
        super().validate(value)

    def lookup_member(self, member_name):
        return DictField(db_field=member_name)

    def prepare_query_value(self, op, value):
        match_operators = [*STRING_OPERATORS]

        if op in match_operators and isinstance(value, str):
            return StringField().prepare_query_value(op, value)

        if hasattr(
            self.field, "field"
        ):  # Used for instance when using DictField(ListField(IntField()))
            if op in ("set", "unset") and isinstance(value, dict):
                return {
                    k: self.field.prepare_query_value(op, v) for k, v in value.items()
                }
            return self.field.prepare_query_value(op, value)

        return super().prepare_query_value(op, value)


class MapField(DictField):
    """A field that maps a name to a specified field type. Similar to
    a DictField, except the 'value' of each item must match the specified
    field type.
    """

    def __init__(self, field=None, *args, **kwargs):
        # XXX ValidationError raised outside of the "validate" method.
        if not isinstance(field, BaseField):
            self.error("Argument to MapField constructor must be a valid field")
        super().__init__(field=field, *args, **kwargs)


class ReferenceField(BaseField):
    """A reference to a document that will be automatically dereferenced on
    access (lazily).

    Note this means you will get a database I/O access everytime you access
    this field. This is necessary because the field returns a :class:`~mongoengine.Document`
    which precise type can depend of the value of the `_cls` field present in the
    document in database.
    In short, using this type of field can lead to poor performances (especially
    if you access this field only to retrieve it `pk` field which is already
    known before dereference). To solve this you should consider using the
    :class:`~mongoengine.fields.LazyReferenceField`.

    Use the `reverse_delete_rule` to handle what should happen if the document
    the field is referencing is deleted.  EmbeddedDocuments, DictFields and
    MapFields does not support reverse_delete_rule and an `InvalidDocumentError`
    will be raised if trying to set on one of these Document / Field types.

    The options are:

      * DO_NOTHING (0)  - don't do anything (default).
      * NULLIFY    (1)  - Updates the reference to null.
      * CASCADE    (2)  - Deletes the documents associated with the reference.
      * DENY       (3)  - Prevent the deletion of the reference object.
      * PULL       (4)  - Pull the reference from a :class:`~mongoengine.fields.ListField` of references

    Alternative syntax for registering delete rules (useful when implementing
    bi-directional delete rules)

    .. code-block:: python

        class Org(Document):
            owner = ReferenceField('User')

        class User(Document):
            org = ReferenceField('Org', reverse_delete_rule=CASCADE)

        User.register_delete_rule(Org, 'owner', DENY)
    """

    def __init__(
        self, document_type, dbref=False, reverse_delete_rule=DO_NOTHING, **kwargs
    ):
        """Initialises the Reference Field.

        :param document_type: The type of Document that will be referenced
        :param dbref:  Store the reference as :class:`~pymongo.dbref.DBRef`
          or as the :class:`~pymongo.objectid.ObjectId`.
        :param reverse_delete_rule: Determines what to do when the referring
          object is deleted
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.BaseField`

        .. note ::
            A reference to an abstract document type is always stored as a
            :class:`~pymongo.dbref.DBRef`, regardless of the value of `dbref`.
        """
        # XXX ValidationError raised outside of the "validate" method.
        if not isinstance(document_type, str) and not issubclass(
            document_type, Document
        ):
            self.error(
                "Argument to ReferenceField constructor must be a "
                "document class or a string"
            )

        self.dbref = dbref
        self.document_type_obj = document_type
        self.reverse_delete_rule = reverse_delete_rule
        super().__init__(**kwargs)

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, str):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
            else:
                self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    @staticmethod
    def _lazy_load_ref(ref_cls, dbref):
        dereferenced_son = ref_cls._get_db().dereference(dbref)
        if dereferenced_son is None:
            raise DoesNotExist(f"Trying to dereference unknown document {dbref}")

        return ref_cls._from_son(dereferenced_son)

    def __get__(self, instance, owner):
        """Descriptor to allow lazy dereferencing."""
        if instance is None:
            # Document class being used rather than a document object
            return self

        # Get value from document instance if available
        ref_value = instance._data.get(self.name)
        auto_dereference = instance._fields[self.name]._auto_dereference
        # Dereference DBRefs
        if auto_dereference and isinstance(ref_value, DBRef):
            if hasattr(ref_value, "cls"):
                # Dereference using the class type specified in the reference
                cls = get_document(ref_value.cls)
            else:
                cls = self.document_type

            instance._data[self.name] = self._lazy_load_ref(cls, ref_value)

        return super().__get__(instance, owner)

    def to_mongo(self, document):
        if isinstance(document, DBRef):
            if not self.dbref:
                return document.id
            return document

        if isinstance(document, Document):
            # We need the id from the saved object to create the DBRef
            id_ = document.pk

            # XXX ValidationError raised outside of the "validate" method.
            if id_ is None:
                self.error(
                    "You can only reference documents once they have"
                    " been saved to the database"
                )

            # Use the attributes from the document instance, so that they
            # override the attributes of this field's document type
            cls = document
        else:
            id_ = document
            cls = self.document_type

        id_field_name = cls._meta["id_field"]
        id_field = cls._fields[id_field_name]

        id_ = id_field.to_mongo(id_)
        if self.document_type._meta.get("abstract"):
            collection = cls._get_collection_name()
            return DBRef(collection, id_, cls=cls._class_name)
        elif self.dbref:
            collection = cls._get_collection_name()
            return DBRef(collection, id_)

        return id_

    def to_python(self, value):
        """Convert a MongoDB-compatible type to a Python type."""
        if not self.dbref and not isinstance(
            value, (DBRef, Document, EmbeddedDocument)
        ):
            collection = self.document_type._get_collection_name()
            value = DBRef(collection, self.document_type.id.to_python(value))
        return value

    def prepare_query_value(self, op, value):
        if value is None:
            return None
        super().prepare_query_value(op, value)
        return self.to_mongo(value)

    def validate(self, value):
        if not isinstance(value, (self.document_type, LazyReference, DBRef, ObjectId)):
            self.error(
                "A ReferenceField only accepts DBRef, LazyReference, ObjectId or documents"
            )

        if isinstance(value, Document) and value.id is None:
            self.error(
                "You can only reference documents once they have been "
                "saved to the database"
            )

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)


class CachedReferenceField(BaseField):
    """A referencefield with cache fields to purpose pseudo-joins"""

    def __init__(self, document_type, fields=None, auto_sync=True, **kwargs):
        """Initialises the Cached Reference Field.

        :param document_type: The type of Document that will be referenced
        :param fields:  A list of fields to be cached in document
        :param auto_sync: if True documents are auto updated
        :param kwargs: Keyword arguments passed into the parent :class:`~mongoengine.BaseField`
        """
        if fields is None:
            fields = []

        # XXX ValidationError raised outside of the "validate" method.
        if not isinstance(document_type, str) and not (
            inspect.isclass(document_type) and issubclass(document_type, Document)
        ):
            self.error(
                "Argument to CachedReferenceField constructor must be a"
                " document class or a string"
            )

        self.auto_sync = auto_sync
        self.document_type_obj = document_type
        self.fields = fields
        super().__init__(**kwargs)

    def start_listener(self):
        from mongoengine import signals

        signals.post_save.connect(self.on_document_pre_save, sender=self.document_type)

    def on_document_pre_save(self, sender, document, created, **kwargs):
        if created:
            return None

        update_kwargs = {
            f"set__{self.name}__{key}": val
            for key, val in document._delta()[0].items()
            if key in self.fields
        }
        if update_kwargs:
            filter_kwargs = {}
            filter_kwargs[self.name] = document

            self.owner_document.objects(**filter_kwargs).update(**update_kwargs)

    def to_python(self, value):
        if isinstance(value, dict):
            collection = self.document_type._get_collection_name()
            value = DBRef(collection, self.document_type.id.to_python(value["_id"]))
            return self.document_type._from_son(
                self.document_type._get_db().dereference(value)
            )

        return value

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, str):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
            else:
                self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    @staticmethod
    def _lazy_load_ref(ref_cls, dbref):
        dereferenced_son = ref_cls._get_db().dereference(dbref)
        if dereferenced_son is None:
            raise DoesNotExist(f"Trying to dereference unknown document {dbref}")

        return ref_cls._from_son(dereferenced_son)

    def __get__(self, instance, owner):
        if instance is None:
            # Document class being used rather than a document object
            return self

        # Get value from document instance if available
        value = instance._data.get(self.name)
        auto_dereference = instance._fields[self.name]._auto_dereference

        # Dereference DBRefs
        if auto_dereference and isinstance(value, DBRef):
            instance._data[self.name] = self._lazy_load_ref(self.document_type, value)

        return super().__get__(instance, owner)

    def to_mongo(self, document, use_db_field=True, fields=None):
        id_field_name = self.document_type._meta["id_field"]
        id_field = self.document_type._fields[id_field_name]

        # XXX ValidationError raised outside of the "validate" method.
        if isinstance(document, Document):
            # We need the id from the saved object to create the DBRef
            id_ = document.pk
            if id_ is None:
                self.error(
                    "You can only reference documents once they have"
                    " been saved to the database"
                )
        else:
            self.error("Only accept a document object")

        value = SON((("_id", id_field.to_mongo(id_)),))

        if fields:
            new_fields = [f for f in self.fields if f in fields]
        else:
            new_fields = self.fields

        value.update(dict(document.to_mongo(use_db_field, fields=new_fields)))
        return value

    def prepare_query_value(self, op, value):
        if value is None:
            return None

        # XXX ValidationError raised outside of the "validate" method.
        if isinstance(value, Document):
            if value.pk is None:
                self.error(
                    "You can only reference documents once they have"
                    " been saved to the database"
                )
            value_dict = {"_id": value.pk}
            for field in self.fields:
                value_dict.update({field: value[field]})

            return value_dict

        raise NotImplementedError

    def validate(self, value):
        if not isinstance(value, self.document_type):
            self.error("A CachedReferenceField only accepts documents")

        if isinstance(value, Document) and value.id is None:
            self.error(
                "You can only reference documents once they have been "
                "saved to the database"
            )

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)

    def sync_all(self):
        """
        Sync all cached fields on demand.
        Caution: this operation may be slower.
        """
        update_key = "set__%s" % self.name

        for doc in self.document_type.objects:
            filter_kwargs = {}
            filter_kwargs[self.name] = doc

            update_kwargs = {}
            update_kwargs[update_key] = doc

            self.owner_document.objects(**filter_kwargs).update(**update_kwargs)


class GenericReferenceField(BaseField):
    """A reference to *any* :class:`~mongoengine.document.Document` subclass
    that will be automatically dereferenced on access (lazily).

    Note this field works the same way as :class:`~mongoengine.document.ReferenceField`,
    doing database I/O access the first time it is accessed (even if it's to access
    it ``pk`` or ``id`` field).
    To solve this you should consider using the
    :class:`~mongoengine.fields.GenericLazyReferenceField`.

    .. note ::
        * Any documents used as a generic reference must be registered in the
          document registry.  Importing the model will automatically register
          it.

        * You can use the choices param to limit the acceptable Document types
    """

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", None)
        super().__init__(*args, **kwargs)
        self.choices = []
        # Keep the choices as a list of allowed Document class names
        if choices:
            for choice in choices:
                if isinstance(choice, str):
                    self.choices.append(choice)
                elif isinstance(choice, type) and issubclass(choice, Document):
                    self.choices.append(choice._class_name)
                else:
                    # XXX ValidationError raised outside of the "validate"
                    # method.
                    self.error(
                        "Invalid choices provided: must be a list of"
                        "Document subclasses and/or str"
                    )

    def _validate_choices(self, value):
        if isinstance(value, dict):
            # If the field has not been dereferenced, it is still a dict
            # of class and DBRef
            value = value.get("_cls")
        elif isinstance(value, Document):
            value = value._class_name
        super()._validate_choices(value)

    @staticmethod
    def _lazy_load_ref(ref_cls, dbref):
        dereferenced_son = ref_cls._get_db().dereference(dbref)
        if dereferenced_son is None:
            raise DoesNotExist(f"Trying to dereference unknown document {dbref}")

        return ref_cls._from_son(dereferenced_son)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = instance._data.get(self.name)

        auto_dereference = instance._fields[self.name]._auto_dereference
        if auto_dereference and isinstance(value, dict):
            doc_cls = get_document(value["_cls"])
            instance._data[self.name] = self._lazy_load_ref(doc_cls, value["_ref"])

        return super().__get__(instance, owner)

    def validate(self, value):
        if not isinstance(value, (Document, DBRef, dict, SON)):
            self.error("GenericReferences can only contain documents")

        if isinstance(value, (dict, SON)):
            if "_ref" not in value or "_cls" not in value:
                self.error("GenericReferences can only contain documents")

        # We need the id from the saved object to create the DBRef
        elif isinstance(value, Document) and value.id is None:
            self.error(
                "You can only reference documents once they have been"
                " saved to the database"
            )

    def to_mongo(self, document):
        if document is None:
            return None

        if isinstance(document, (dict, SON, ObjectId, DBRef)):
            return document

        id_field_name = document.__class__._meta["id_field"]
        id_field = document.__class__._fields[id_field_name]

        if isinstance(document, Document):
            # We need the id from the saved object to create the DBRef
            id_ = document.id
            if id_ is None:
                # XXX ValidationError raised outside of the "validate" method.
                self.error(
                    "You can only reference documents once they have"
                    " been saved to the database"
                )
        else:
            id_ = document

        id_ = id_field.to_mongo(id_)
        collection = document._get_collection_name()
        ref = DBRef(collection, id_)
        return SON((("_cls", document._class_name), ("_ref", ref)))

    def prepare_query_value(self, op, value):
        if value is None:
            return None

        return self.to_mongo(value)


class BinaryField(BaseField):
    """A binary data field."""

    def __init__(self, max_bytes=None, **kwargs):
        self.max_bytes = max_bytes
        super().__init__(**kwargs)

    def __set__(self, instance, value):
        """Handle bytearrays in python 3.1"""
        if isinstance(value, bytearray):
            value = bytes(value)
        return super().__set__(instance, value)

    def to_mongo(self, value):
        return Binary(value)

    def validate(self, value):
        if not isinstance(value, (bytes, Binary)):
            self.error(
                "BinaryField only accepts instances of "
                "(%s, %s, Binary)" % (bytes.__name__, Binary.__name__)
            )

        if self.max_bytes is not None and len(value) > self.max_bytes:
            self.error("Binary value is too long")

    def prepare_query_value(self, op, value):
        if value is None:
            return value
        return super().prepare_query_value(op, self.to_mongo(value))


class EnumField(BaseField):
    """Enumeration Field. Values are stored underneath as is,
    so it will only work with simple types (str, int, etc) that
    are bson encodable

    Example usage:

    .. code-block:: python

        class Status(Enum):
            NEW = 'new'
            ONGOING = 'ongoing'
            DONE = 'done'

        class ModelWithEnum(Document):
            status = EnumField(Status, default=Status.NEW)

        ModelWithEnum(status='done')
        ModelWithEnum(status=Status.DONE)

    Enum fields can be searched using enum or its value:

    .. code-block:: python

        ModelWithEnum.objects(status='new').count()
        ModelWithEnum.objects(status=Status.NEW).count()

    The values can be restricted to a subset of the enum by using the ``choices`` parameter:

    .. code-block:: python

        class ModelWithEnum(Document):
            status = EnumField(Status, choices=[Status.NEW, Status.DONE])
    """

    def __init__(self, enum, **kwargs):
        self._enum_cls = enum
        if kwargs.get("choices"):
            invalid_choices = []
            for choice in kwargs["choices"]:
                if not isinstance(choice, enum):
                    invalid_choices.append(choice)
            if invalid_choices:
                raise ValueError("Invalid choices: %r" % invalid_choices)
        else:
            kwargs["choices"] = list(self._enum_cls)  # Implicit validator
        super().__init__(**kwargs)

    def __set__(self, instance, value):
        is_legal_value = value is None or isinstance(value, self._enum_cls)
        if not is_legal_value:
            try:
                value = self._enum_cls(value)
            except Exception:
                pass
        return super().__set__(instance, value)

    def to_mongo(self, value):
        if isinstance(value, self._enum_cls):
            return value.value
        return value

    def prepare_query_value(self, op, value):
        if value is None:
            return value
        return super().prepare_query_value(op, self.to_mongo(value))


class GridFSError(Exception):
    pass


class GridFSProxy:
    """Proxy object to handle writing and reading of files to and from GridFS"""

    _fs = None

    def __init__(
        self,
        grid_id=None,
        key=None,
        instance=None,
        db_alias=DEFAULT_CONNECTION_NAME,
        collection_name="fs",
    ):
        self.grid_id = grid_id  # Store GridFS id for file
        self.key = key
        self.instance = instance
        self.db_alias = db_alias
        self.collection_name = collection_name
        self.newfile = None  # Used for partial writes
        self.gridout = None

    def __getattr__(self, name):
        attrs = (
            "_fs",
            "grid_id",
            "key",
            "instance",
            "db_alias",
            "collection_name",
            "newfile",
            "gridout",
        )
        if name in attrs:
            return self.__getattribute__(name)
        obj = self.get()
        if hasattr(obj, name):
            return getattr(obj, name)
        raise AttributeError

    def __get__(self, instance, value):
        return self

    def __bool__(self):
        return bool(self.grid_id)

    def __getstate__(self):
        self_dict = self.__dict__
        self_dict["_fs"] = None
        return self_dict

    def __copy__(self):
        copied = GridFSProxy()
        copied.__dict__.update(self.__getstate__())
        return copied

    def __deepcopy__(self, memo):
        return self.__copy__()

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.grid_id}>"

    def __str__(self):
        gridout = self.get()
        filename = gridout.filename if gridout else "<no file>"
        return f"<{self.__class__.__name__}: {filename} ({self.grid_id})>"

    def __eq__(self, other):
        if isinstance(other, GridFSProxy):
            return (
                (self.grid_id == other.grid_id)
                and (self.collection_name == other.collection_name)
                and (self.db_alias == other.db_alias)
            )
        else:
            return False

    def __ne__(self, other):
        return not self == other

    @property
    def fs(self):
        if not self._fs:
            self._fs = gridfs.GridFS(get_db(self.db_alias), self.collection_name)
        return self._fs

    def get(self, grid_id=None):
        if grid_id:
            self.grid_id = grid_id

        if self.grid_id is None:
            return None

        try:
            if self.gridout is None:
                self.gridout = self.fs.get(self.grid_id)
            return self.gridout
        except Exception:
            # File has been deleted
            return None

    def new_file(self, **kwargs):
        self.newfile = self.fs.new_file(**kwargs)
        self.grid_id = self.newfile._id
        self._mark_as_changed()

    def put(self, file_obj, **kwargs):
        if self.grid_id:
            raise GridFSError(
                "This document already has a file. Either delete "
                "it or call replace to overwrite it"
            )
        self.grid_id = self.fs.put(file_obj, **kwargs)
        self._mark_as_changed()

    def write(self, string):
        if self.grid_id:
            if not self.newfile:
                raise GridFSError(
                    "This document already has a file. Either "
                    "delete it or call replace to overwrite it"
                )
        else:
            self.new_file()
        self.newfile.write(string)

    def writelines(self, lines):
        if not self.newfile:
            self.new_file()
            self.grid_id = self.newfile._id
        self.newfile.writelines(lines)

    def read(self, size=-1):
        gridout = self.get()
        if gridout is None:
            return None
        else:
            try:
                return gridout.read(size)
            except Exception:
                return ""

    def delete(self):
        # Delete file from GridFS, FileField still remains
        self.fs.delete(self.grid_id)
        self.grid_id = None
        self.gridout = None
        self._mark_as_changed()

    def replace(self, file_obj, **kwargs):
        self.delete()
        self.put(file_obj, **kwargs)

    def close(self):
        if self.newfile:
            self.newfile.close()

    def _mark_as_changed(self):
        """Inform the instance that `self.key` has been changed"""
        if self.instance:
            self.instance._mark_as_changed(self.key)


class FileField(BaseField):
    """A GridFS storage field."""

    proxy_class = GridFSProxy

    def __init__(
        self, db_alias=DEFAULT_CONNECTION_NAME, collection_name="fs", **kwargs
    ):
        super().__init__(**kwargs)
        self.collection_name = collection_name
        self.db_alias = db_alias

    def __get__(self, instance, owner):
        if instance is None:
            return self

        # Check if a file already exists for this model
        grid_file = instance._data.get(self.name)
        if not isinstance(grid_file, self.proxy_class):
            grid_file = self.get_proxy_obj(key=self.name, instance=instance)
            instance._data[self.name] = grid_file

        if not grid_file.key:
            grid_file.key = self.name
            grid_file.instance = instance
        return grid_file

    def __set__(self, instance, value):
        key = self.name
        if (
            hasattr(value, "read") and not isinstance(value, GridFSProxy)
        ) or isinstance(value, (bytes, str)):
            # using "FileField() = file/string" notation
            grid_file = instance._data.get(self.name)
            # If a file already exists, delete it
            if grid_file:
                try:
                    grid_file.delete()
                except Exception:
                    pass

            # Create a new proxy object as we don't already have one
            instance._data[key] = self.get_proxy_obj(key=key, instance=instance)
            instance._data[key].put(value)
        else:
            instance._data[key] = value

        instance._mark_as_changed(key)

    def get_proxy_obj(self, key, instance, db_alias=None, collection_name=None):
        if db_alias is None:
            db_alias = self.db_alias
        if collection_name is None:
            collection_name = self.collection_name

        return self.proxy_class(
            key=key,
            instance=instance,
            db_alias=db_alias,
            collection_name=collection_name,
        )

    def to_mongo(self, value):
        # Store the GridFS file id in MongoDB
        if isinstance(value, self.proxy_class) and value.grid_id is not None:
            return value.grid_id
        return None

    def to_python(self, value):
        if value is not None:
            return self.proxy_class(
                value, collection_name=self.collection_name, db_alias=self.db_alias
            )

    def validate(self, value):
        if value.grid_id is not None:
            if not isinstance(value, self.proxy_class):
                self.error("FileField only accepts GridFSProxy values")
            if not isinstance(value.grid_id, ObjectId):
                self.error("Invalid GridFSProxy value")


class ImageGridFsProxy(GridFSProxy):
    """Proxy for ImageField"""

    def put(self, file_obj, **kwargs):
        """
        Insert a image in database
        applying field properties (size, thumbnail_size)
        """
        field = self.instance._fields[self.key]
        # Handle nested fields
        if hasattr(field, "field") and isinstance(field.field, FileField):
            field = field.field

        try:
            img = Image.open(file_obj)
            img_format = img.format
        except Exception as e:
            raise ValidationError("Invalid image: %s" % e)

        # Progressive JPEG
        # TODO: fixme, at least unused, at worst bad implementation
        progressive = img.info.get("progressive") or False

        if (
            kwargs.get("progressive")
            and isinstance(kwargs.get("progressive"), bool)
            and img_format == "JPEG"
        ):
            progressive = True
        else:
            progressive = False

        if field.size and (
            img.size[0] > field.size["width"] or img.size[1] > field.size["height"]
        ):
            size = field.size

            if size["force"]:
                img = ImageOps.fit(
                    img, (size["width"], size["height"]), Image.ANTIALIAS
                )
            else:
                img.thumbnail((size["width"], size["height"]), Image.ANTIALIAS)

        thumbnail = None
        if field.thumbnail_size:
            size = field.thumbnail_size

            if size["force"]:
                thumbnail = ImageOps.fit(
                    img, (size["width"], size["height"]), Image.ANTIALIAS
                )
            else:
                thumbnail = img.copy()
                thumbnail.thumbnail((size["width"], size["height"]), Image.ANTIALIAS)

        if thumbnail:
            thumb_id = self._put_thumbnail(thumbnail, img_format, progressive)
        else:
            thumb_id = None

        w, h = img.size

        io = BytesIO()
        img.save(io, img_format, progressive=progressive)
        io.seek(0)

        return super().put(
            io, width=w, height=h, format=img_format, thumbnail_id=thumb_id, **kwargs
        )

    def delete(self, *args, **kwargs):
        # deletes thumbnail
        out = self.get()
        if out and out.thumbnail_id:
            self.fs.delete(out.thumbnail_id)

        return super().delete()

    def _put_thumbnail(self, thumbnail, format, progressive, **kwargs):
        w, h = thumbnail.size

        io = BytesIO()
        thumbnail.save(io, format, progressive=progressive)
        io.seek(0)

        return self.fs.put(io, width=w, height=h, format=format, **kwargs)

    @property
    def size(self):
        """
        return a width, height of image
        """
        out = self.get()
        if out:
            return out.width, out.height

    @property
    def format(self):
        """
        return format of image
        ex: PNG, JPEG, GIF, etc
        """
        out = self.get()
        if out:
            return out.format

    @property
    def thumbnail(self):
        """
        return a gridfs.grid_file.GridOut
        representing a thumbnail of Image
        """
        out = self.get()
        if out and out.thumbnail_id:
            return self.fs.get(out.thumbnail_id)

    def write(self, *args, **kwargs):
        raise RuntimeError('Please use "put" method instead')

    def writelines(self, *args, **kwargs):
        raise RuntimeError('Please use "put" method instead')


class ImproperlyConfigured(Exception):
    pass


class ImageField(FileField):
    """
    A Image File storage field.

    :param size: max size to store images, provided as (width, height, force)
        if larger, it will be automatically resized (ex: size=(800, 600, True))
    :param thumbnail_size: size to generate a thumbnail, provided as (width, height, force)
    """

    proxy_class = ImageGridFsProxy

    def __init__(
        self, size=None, thumbnail_size=None, collection_name="images", **kwargs
    ):
        if not Image:
            raise ImproperlyConfigured("PIL library was not found")

        params_size = ("width", "height", "force")
        extra_args = {"size": size, "thumbnail_size": thumbnail_size}
        for att_name, att in extra_args.items():
            value = None
            if isinstance(att, (tuple, list)):
                value = dict(itertools.zip_longest(params_size, att, fillvalue=None))

            setattr(self, att_name, value)

        super().__init__(collection_name=collection_name, **kwargs)


class SequenceField(BaseField):
    """Provides a sequential counter see:
     https://docs.mongodb.com/manual/reference/method/ObjectId/#ObjectIDs-SequenceNumbers

    .. note::

             Although traditional databases often use increasing sequence
             numbers for primary keys. In MongoDB, the preferred approach is to
             use Object IDs instead.  The concept is that in a very large
             cluster of machines, it is easier to create an object ID than have
             global, uniformly increasing sequence numbers.

    :param collection_name:  Name of the counter collection (default 'mongoengine.counters')
    :param sequence_name: Name of the sequence in the collection (default 'ClassName.counter')
    :param value_decorator: Any callable to use as a counter (default int)

    Use any callable as `value_decorator` to transform calculated counter into
    any value suitable for your needs, e.g. string or hexadecimal
    representation of the default integer counter value.

    .. note::

        In case the counter is defined in the abstract document, it will be
        common to all inherited documents and the default sequence name will
        be the class name of the abstract document.
    """

    _auto_gen = True
    COLLECTION_NAME = "mongoengine.counters"
    VALUE_DECORATOR = int

    def __init__(
        self,
        collection_name=None,
        db_alias=None,
        sequence_name=None,
        value_decorator=None,
        *args,
        **kwargs,
    ):
        self.collection_name = collection_name or self.COLLECTION_NAME
        self.db_alias = db_alias or DEFAULT_CONNECTION_NAME
        self.sequence_name = sequence_name
        self.value_decorator = (
            value_decorator if callable(value_decorator) else self.VALUE_DECORATOR
        )
        super().__init__(*args, **kwargs)

    def generate(self):
        """
        Generate and Increment the counter
        """
        sequence_name = self.get_sequence_name()
        sequence_id = f"{sequence_name}.{self.name}"
        collection = get_db(alias=self.db_alias)[self.collection_name]

        counter = collection.find_one_and_update(
            filter={"_id": sequence_id},
            update={"$inc": {"next": 1}},
            return_document=ReturnDocument.AFTER,
            upsert=True,
        )
        return self.value_decorator(counter["next"])

    def set_next_value(self, value):
        """Helper method to set the next sequence value"""
        sequence_name = self.get_sequence_name()
        sequence_id = f"{sequence_name}.{self.name}"
        collection = get_db(alias=self.db_alias)[self.collection_name]
        counter = collection.find_one_and_update(
            filter={"_id": sequence_id},
            update={"$set": {"next": value}},
            return_document=ReturnDocument.AFTER,
            upsert=True,
        )
        return self.value_decorator(counter["next"])

    def get_next_value(self):
        """Helper method to get the next value for previewing.

        .. warning:: There is no guarantee this will be the next value
        as it is only fixed on set.
        """
        sequence_name = self.get_sequence_name()
        sequence_id = f"{sequence_name}.{self.name}"
        collection = get_db(alias=self.db_alias)[self.collection_name]
        data = collection.find_one({"_id": sequence_id})

        if data:
            return self.value_decorator(data["next"] + 1)

        return self.value_decorator(1)

    def get_sequence_name(self):
        if self.sequence_name:
            return self.sequence_name
        owner = self.owner_document
        if issubclass(owner, Document) and not owner._meta.get("abstract"):
            return owner._get_collection_name()
        else:
            return (
                "".join("_%s" % c if c.isupper() else c for c in owner._class_name)
                .strip("_")
                .lower()
            )

    def __get__(self, instance, owner):
        value = super().__get__(instance, owner)
        if value is None and instance._initialised:
            value = self.generate()
            instance._data[self.name] = value
            instance._mark_as_changed(self.name)

        return value

    def __set__(self, instance, value):

        if value is None and instance._initialised:
            value = self.generate()

        return super().__set__(instance, value)

    def prepare_query_value(self, op, value):
        """
        This method is overridden in order to convert the query value into to required
        type. We need to do this in order to be able to successfully compare query
        values passed as string, the base implementation returns the value as is.
        """
        return self.value_decorator(value)

    def to_python(self, value):
        if value is None:
            value = self.generate()
        return value


class UUIDField(BaseField):
    """A UUID field."""

    _binary = None

    def __init__(self, binary=True, **kwargs):
        """
        Store UUID data in the database

        :param binary: if False store as a string.
        """
        self._binary = binary
        super().__init__(**kwargs)

    def to_python(self, value):
        if not self._binary:
            original_value = value
            try:
                if not isinstance(value, str):
                    value = str(value)
                return uuid.UUID(value)
            except (ValueError, TypeError, AttributeError):
                return original_value
        return value

    def to_mongo(self, value):
        if not self._binary:
            return str(value)
        elif isinstance(value, str):
            return uuid.UUID(value)
        return value

    def prepare_query_value(self, op, value):
        if value is None:
            return None
        return self.to_mongo(value)

    def validate(self, value):
        if not isinstance(value, uuid.UUID):
            if not isinstance(value, str):
                value = str(value)
            try:
                uuid.UUID(value)
            except (ValueError, TypeError, AttributeError) as exc:
                self.error("Could not convert to UUID: %s" % exc)


class GeoPointField(BaseField):
    """A list storing a longitude and latitude coordinate.

    .. note:: this represents a generic point in a 2D plane and a legacy way of
        representing a geo point. It admits 2d indexes but not "2dsphere" indexes
        in MongoDB > 2.4 which are more natural for modeling geospatial points.
        See :ref:`geospatial-indexes`
    """

    _geo_index = pymongo.GEO2D

    def validate(self, value):
        """Make sure that a geo-value is of type (x, y)"""
        if not isinstance(value, (list, tuple)):
            self.error("GeoPointField can only accept tuples or lists of (x, y)")

        if not len(value) == 2:
            self.error("Value (%s) must be a two-dimensional point" % repr(value))
        elif not isinstance(value[0], (float, int)) or not isinstance(
            value[1], (float, int)
        ):
            self.error("Both values (%s) in point must be float or int" % repr(value))


class PointField(GeoJsonBaseField):
    """A GeoJSON field storing a longitude and latitude coordinate.

    The data is represented as:

    .. code-block:: js

        {'type' : 'Point' ,
         'coordinates' : [x, y]}

    You can either pass a dict with the full information or a list
    to set the value.

    Requires mongodb >= 2.4
    """

    _type = "Point"


class LineStringField(GeoJsonBaseField):
    """A GeoJSON field storing a line of longitude and latitude coordinates.

    The data is represented as:

    .. code-block:: js

        {'type' : 'LineString' ,
         'coordinates' : [[x1, y1], [x2, y2] ... [xn, yn]]}

    You can either pass a dict with the full information or a list of points.

    Requires mongodb >= 2.4
    """

    _type = "LineString"


class PolygonField(GeoJsonBaseField):
    """A GeoJSON field storing a polygon of longitude and latitude coordinates.

    The data is represented as:

    .. code-block:: js

        {'type' : 'Polygon' ,
         'coordinates' : [[[x1, y1], [x1, y1] ... [xn, yn]],
                          [[x1, y1], [x1, y1] ... [xn, yn]]}

    You can either pass a dict with the full information or a list
    of LineStrings. The first LineString being the outside and the rest being
    holes.

    Requires mongodb >= 2.4
    """

    _type = "Polygon"


class MultiPointField(GeoJsonBaseField):
    """A GeoJSON field storing a list of Points.

    The data is represented as:

    .. code-block:: js

        {'type' : 'MultiPoint' ,
         'coordinates' : [[x1, y1], [x2, y2]]}

    You can either pass a dict with the full information or a list
    to set the value.

    Requires mongodb >= 2.6
    """

    _type = "MultiPoint"


class MultiLineStringField(GeoJsonBaseField):
    """A GeoJSON field storing a list of LineStrings.

    The data is represented as:

    .. code-block:: js

        {'type' : 'MultiLineString' ,
         'coordinates' : [[[x1, y1], [x1, y1] ... [xn, yn]],
                          [[x1, y1], [x1, y1] ... [xn, yn]]]}

    You can either pass a dict with the full information or a list of points.

    Requires mongodb >= 2.6
    """

    _type = "MultiLineString"


class MultiPolygonField(GeoJsonBaseField):
    """A GeoJSON field storing  list of Polygons.

    The data is represented as:

    .. code-block:: js

        {'type' : 'MultiPolygon' ,
         'coordinates' : [[
               [[x1, y1], [x1, y1] ... [xn, yn]],
               [[x1, y1], [x1, y1] ... [xn, yn]]
           ], [
               [[x1, y1], [x1, y1] ... [xn, yn]],
               [[x1, y1], [x1, y1] ... [xn, yn]]
           ]
        }

    You can either pass a dict with the full information or a list
    of Polygons.

    Requires mongodb >= 2.6
    """

    _type = "MultiPolygon"


class LazyReferenceField(BaseField):
    """A really lazy reference to a document.
    Unlike the :class:`~mongoengine.fields.ReferenceField` it will
    **not** be automatically (lazily) dereferenced on access.
    Instead, access will return a :class:`~mongoengine.base.LazyReference` class
    instance, allowing access to `pk` or manual dereference by using
    ``fetch()`` method.
    """

    def __init__(
        self,
        document_type,
        passthrough=False,
        dbref=False,
        reverse_delete_rule=DO_NOTHING,
        **kwargs,
    ):
        """Initialises the Reference Field.

        :param dbref:  Store the reference as :class:`~pymongo.dbref.DBRef`
          or as the :class:`~pymongo.objectid.ObjectId`.id .
        :param reverse_delete_rule: Determines what to do when the referring
          object is deleted
        :param passthrough: When trying to access unknown fields, the
          :class:`~mongoengine.base.datastructure.LazyReference` instance will
          automatically call `fetch()` and try to retrieve the field on the fetched
          document. Note this only work getting field (not setting or deleting).
        """
        # XXX ValidationError raised outside of the "validate" method.
        if not isinstance(document_type, str) and not issubclass(
            document_type, Document
        ):
            self.error(
                "Argument to LazyReferenceField constructor must be a "
                "document class or a string"
            )

        self.dbref = dbref
        self.passthrough = passthrough
        self.document_type_obj = document_type
        self.reverse_delete_rule = reverse_delete_rule
        super().__init__(**kwargs)

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, str):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
            else:
                self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    def build_lazyref(self, value):
        if isinstance(value, LazyReference):
            if value.passthrough != self.passthrough:
                value = LazyReference(
                    value.document_type, value.pk, passthrough=self.passthrough
                )
        elif value is not None:
            if isinstance(value, self.document_type):
                value = LazyReference(
                    self.document_type, value.pk, passthrough=self.passthrough
                )
            elif isinstance(value, DBRef):
                value = LazyReference(
                    self.document_type, value.id, passthrough=self.passthrough
                )
            else:
                # value is the primary key of the referenced document
                value = LazyReference(
                    self.document_type, value, passthrough=self.passthrough
                )
        return value

    def __get__(self, instance, owner):
        """Descriptor to allow lazy dereferencing."""
        if instance is None:
            # Document class being used rather than a document object
            return self

        value = self.build_lazyref(instance._data.get(self.name))
        if value:
            instance._data[self.name] = value

        return super().__get__(instance, owner)

    def to_mongo(self, value):
        if isinstance(value, LazyReference):
            pk = value.pk
        elif isinstance(value, self.document_type):
            pk = value.pk
        elif isinstance(value, DBRef):
            pk = value.id
        else:
            # value is the primary key of the referenced document
            pk = value
        id_field_name = self.document_type._meta["id_field"]
        id_field = self.document_type._fields[id_field_name]
        pk = id_field.to_mongo(pk)
        if self.dbref:
            return DBRef(self.document_type._get_collection_name(), pk)
        else:
            return pk

    def to_python(self, value):
        """Convert a MongoDB-compatible type to a Python type."""
        if not isinstance(value, (DBRef, Document, EmbeddedDocument)):
            collection = self.document_type._get_collection_name()
            value = DBRef(collection, self.document_type.id.to_python(value))
            value = self.build_lazyref(value)
        return value

    def validate(self, value):
        if isinstance(value, LazyReference):
            if value.collection != self.document_type._get_collection_name():
                self.error("Reference must be on a `%s` document." % self.document_type)
            pk = value.pk
        elif isinstance(value, self.document_type):
            pk = value.pk
        elif isinstance(value, DBRef):
            # TODO: check collection ?
            collection = self.document_type._get_collection_name()
            if value.collection != collection:
                self.error("DBRef on bad collection (must be on `%s`)" % collection)
            pk = value.id
        else:
            # value is the primary key of the referenced document
            id_field_name = self.document_type._meta["id_field"]
            id_field = getattr(self.document_type, id_field_name)
            pk = value
            try:
                id_field.validate(pk)
            except ValidationError:
                self.error(
                    "value should be `{0}` document, LazyReference or DBRef on `{0}` "
                    "or `{0}`'s primary key (i.e. `{1}`)".format(
                        self.document_type.__name__, type(id_field).__name__
                    )
                )

        if pk is None:
            self.error(
                "You can only reference documents once they have been "
                "saved to the database"
            )

    def prepare_query_value(self, op, value):
        if value is None:
            return None
        super().prepare_query_value(op, value)
        return self.to_mongo(value)

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)


class GenericLazyReferenceField(GenericReferenceField):
    """A reference to *any* :class:`~mongoengine.document.Document` subclass.
    Unlike the :class:`~mongoengine.fields.GenericReferenceField` it will
    **not** be automatically (lazily) dereferenced on access.
    Instead, access will return a :class:`~mongoengine.base.LazyReference` class
    instance, allowing access to `pk` or manual dereference by using
    ``fetch()`` method.

    .. note ::
        * Any documents used as a generic reference must be registered in the
          document registry.  Importing the model will automatically register
          it.

        * You can use the choices param to limit the acceptable Document types
    """

    def __init__(self, *args, **kwargs):
        self.passthrough = kwargs.pop("passthrough", False)
        super().__init__(*args, **kwargs)

    def _validate_choices(self, value):
        if isinstance(value, LazyReference):
            value = value.document_type._class_name
        super()._validate_choices(value)

    def build_lazyref(self, value):
        if isinstance(value, LazyReference):
            if value.passthrough != self.passthrough:
                value = LazyReference(
                    value.document_type, value.pk, passthrough=self.passthrough
                )
        elif value is not None:
            if isinstance(value, (dict, SON)):
                value = LazyReference(
                    get_document(value["_cls"]),
                    value["_ref"].id,
                    passthrough=self.passthrough,
                )
            elif isinstance(value, Document):
                value = LazyReference(
                    type(value), value.pk, passthrough=self.passthrough
                )
        return value

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = self.build_lazyref(instance._data.get(self.name))
        if value:
            instance._data[self.name] = value

        return super().__get__(instance, owner)

    def validate(self, value):
        if isinstance(value, LazyReference) and value.pk is None:
            self.error(
                "You can only reference documents once they have been"
                " saved to the database"
            )
        return super().validate(value)

    def to_mongo(self, document):
        if document is None:
            return None

        if isinstance(document, LazyReference):
            return SON(
                (
                    ("_cls", document.document_type._class_name),
                    (
                        "_ref",
                        DBRef(
                            document.document_type._get_collection_name(), document.pk
                        ),
                    ),
                )
            )
        else:
            return super().to_mongo(document)
