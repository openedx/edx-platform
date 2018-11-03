from base64 import b64encode
from datetime import (
    datetime,
    timedelta,
    )
from hashlib import md5
import re
import struct
import zlib
try:
    import simplejson as json
except ImportError:
    import json

from webob.byterange import ContentRange

from webob.cachecontrol import (
    CacheControl,
    serialize_cache_control,
    )

from webob.compat import (
    PY2,
    bytes_,
    native_,
    text_type,
    url_quote,
    urlparse,
    )

from webob.cookies import (
    Cookie,
    make_cookie,
    )

from webob.datetime_utils import (
    parse_date_delta,
    serialize_date_delta,
    timedelta_to_seconds,
    )

from webob.descriptors import (
    CHARSET_RE,
    SCHEME_RE,
    converter,
    date_header,
    header_getter,
    list_header,
    parse_auth,
    parse_content_range,
    parse_etag_response,
    parse_int,
    parse_int_safe,
    serialize_auth,
    serialize_content_range,
    serialize_etag_response,
    serialize_int,
    )

from webob.headers import ResponseHeaders
from webob.request import BaseRequest
from webob.util import status_reasons, status_generic_reasons, warn_deprecation

__all__ = ['Response']

_PARAM_RE = re.compile(r'([a-z0-9]+)=(?:"([^"]*)"|([a-z0-9_.-]*))', re.I)
_OK_PARAM_RE = re.compile(r'^[a-z0-9_.-]+$', re.I)

_gzip_header = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff'

_marker = object()

class Response(object):
    """
    Represents a WSGI response.

    If no arguments are passed, creates a :class:`~Response` that uses a
    variety of defaults. The defaults may be changed by sub-classing the
    :class:`~Response`. See the :ref:`sub-classing notes
    <response_subclassing_notes>`.

    :cvar ~Response.body: If ``body`` is a ``text_type``, then it will be
        encoded using either ``charset`` when provided or ``default_encoding``
        when ``charset`` is not provided if the ``content_type`` allows for a
        ``charset``. This argument is mutually  exclusive with ``app_iter``.

    :vartype ~Response.body: bytes or text_type

    :cvar ~Response.status: Either an :class:`int` or a string that is
        an integer followed by the status text. If it is an integer, it will be
        converted to a proper status that also includes the status text.  Any
        existing status text will be kept. Non-standard values are allowed.

    :vartype ~Response.status: int or str

    :cvar ~Response.headerlist: A list of HTTP headers for the response.

    :vartype ~Response.headerlist: list

    :cvar ~Response.app_iter: An iterator that is used as the body of the
        response. Should conform to the WSGI requirements and should provide
        bytes. This argument is mutually exclusive with ``body``.

    :vartype ~Response.app_iter: iterable

    :cvar ~Response.content_type: Sets the ``Content-Type`` header. If no
        ``content_type`` is provided, and there is no ``headerlist``, the
        ``default_content_type`` will be automatically set. If ``headerlist``
        is provided then this value is ignored.

    :vartype ~Response.content_type: str or None

    :cvar conditional_response: Used to change the behavior of the
        :class:`~Response` to check the original request for conditional
        response headers. See :meth:`~Response.conditional_response_app` for
        more information.

    :vartype conditional_response: bool

    :cvar ~Response.charset: Adds a ``charset`` ``Content-Type`` parameter. If
        no ``charset`` is provided and the ``Content-Type`` is text, then the
        ``default_charset`` will automatically be added.  Currently the only
        ``Content-Type``'s that allow for a ``charset`` are defined to be
        ``text/*``, ``application/xml``, and ``*/*+xml``. Any other
        ``Content-Type``'s will not have a ``charset`` added. If a
        ``headerlist`` is provided this value is ignored.

    :vartype ~Response.charset: str or None

    All other response attributes may be set on the response by providing them
    as keyword arguments. A :exc:`TypeError` will be raised for any unexpected
    keywords.

    .. _response_subclassing_notes:

    **Sub-classing notes:**

    * The ``default_content_type`` is used as the default for the
      ``Content-Type`` header that is returned on the response. It is
      ``text/html``.

    * The ``default_charset`` is used as the default character set to return on
      the ``Content-Type`` header, if the ``Content-Type`` allows for a
      ``charset`` parameter. Currently the only ``Content-Type``'s that allow
      for a ``charset`` are defined to be: ``text/*``, ``application/xml``, and
      ``*/*+xml``. Any other ``Content-Type``'s will not have a ``charset``
      added.

    * The ``unicode_errors`` is set to ``strict``, and access on a
      :attr:`~Response.text` will raise an error if it fails to decode the
      :attr:`~Response.body`.

    * ``default_conditional_response`` is set to ``False``. This flag may be
      set to ``True`` so that all ``Response`` objects will attempt to check
      the original request for conditional response headers. See
      :meth:`~Response.conditional_response_app` for more information.

    * ``default_body_encoding`` is set to 'UTF-8' by default. It exists to
      allow users to get/set the ``Response`` object using ``.text``, even if
      no ``charset`` has been set for the ``Content-Type``.
    """

    default_content_type = 'text/html'
    default_charset = 'UTF-8'
    unicode_errors = 'strict'
    default_conditional_response = False
    default_body_encoding = 'UTF-8'

    # These two are only around so that when people pass them into the
    # constructor they correctly get saved and set, however they are not used
    # by any part of the Response. See commit
    # 627593bbcd4ab52adc7ee569001cdda91c670d5d for rationale.
    request = None
    environ = None

    #
    # __init__, from_file, copy
    #

    def __init__(self, body=None, status=None, headerlist=None, app_iter=None,
                 content_type=None, conditional_response=None, charset=_marker,
                 **kw):
        # Do some sanity checking, and turn json_body into an actual body
        if app_iter is None and body is None and ('json_body' in kw or 'json' in kw):
            if 'json_body' in kw:
                json_body = kw.pop('json_body')
            else:
                json_body = kw.pop('json')
            body = json.dumps(json_body, separators=(',', ':')).encode('UTF-8')

            if content_type is None:
                content_type = 'application/json'

        if app_iter is None:
            if body is None:
                body = b''
        elif body is not None:
            raise TypeError(
                "You may only give one of the body and app_iter arguments")

        # Set up Response.status
        if status is None:
            self._status = '200 OK'
        else:
            self.status = status

        # Initialize headers
        self._headers = None
        if headerlist is None:
            self._headerlist = []
        else:
            self._headerlist = headerlist

        # Set the encoding for the Response to charset, so if a charset is
        # passed but the Content-Type does not allow for a charset, we can
        # still encode text_type body's.
        # r = Response(
        #   content_type='application/foo',
        #   charset='UTF-8',
        #   body=u'somebody')
        # Should work without issues, and the header will be correctly set to
        # Content-Type: application/foo with no charset on it.

        encoding = None
        if charset is not _marker:
            encoding = charset

        # Does the status code have a body or not?
        code_has_body = (
            self._status[0] != '1' and
            self._status[:3] not in ('204', '205', '304')
        )

        # We only set the content_type to the one passed to the constructor or
        # the default content type if there is none that exists AND there was
        # no headerlist passed. If a headerlist was provided then most likely
        # the ommission of the Content-Type is on purpose and we shouldn't try
        # to be smart about it.
        #
        # Also allow creation of a empty Response with just the status set to a
        # Response with empty body, such as Response(status='204 No Content')
        # without the default content_type being set (since empty bodies have
        # no Content-Type)
        #
        # Check if content_type is set because default_content_type could be
        # None, in which case there is no content_type, and thus we don't need
        # to anything

        content_type = content_type or self.default_content_type

        if headerlist is None and code_has_body and content_type:
            # Set up the charset, if the content_type doesn't already have one

            has_charset = 'charset=' in content_type

            # If the Content-Type already has a charset, we don't set the user
            # provided charset on the Content-Type, so we shouldn't use it as
            # the encoding for text_type based body's.
            if has_charset:
                encoding = None

            # Do not use the default_charset for the encoding because we
            # want things like
            # Response(content_type='image/jpeg',body=u'foo') to raise when
            # trying to encode the body.

            new_charset = encoding

            if (
                not has_charset and
                charset is _marker and
                self.default_charset
            ):
                new_charset = self.default_charset

            # Optimize for the default_content_type as shipped by
            # WebOb, becuase we know that 'text/html' has a charset,
            # otherwise add a charset if the content_type has a charset.
            #
            # Even if the user supplied charset explicitly, we do not add
            # it to the Content-Type unless it has has a charset, instead
            # the user supplied charset is solely used for encoding the
            # body if it is a text_type

            if (
                new_charset and
                (
                    content_type == 'text/html' or
                    _content_type_has_charset(content_type)
                )
            ):
                content_type += '; charset=' + new_charset

            self._headerlist.append(('Content-Type', content_type))

        # Set up conditional response
        if conditional_response is None:
            self.conditional_response = self.default_conditional_response
        else:
            self.conditional_response = bool(conditional_response)

        # Set up app_iter if the HTTP Status code has a body
        if app_iter is None and code_has_body:
            if isinstance(body, text_type):
                # Fall back to trying self.charset if encoding is not set. In
                # most cases encoding will be set to the default value.
                encoding = encoding or self.charset
                if encoding is None:
                    raise TypeError(
                        "You cannot set the body to a text value without a "
                        "charset")
                body = body.encode(encoding)
            app_iter = [body]

            if headerlist is not None:
                self._headerlist[:] = [
                    (k, v)
                    for (k, v)
                    in self._headerlist
                    if k.lower() != 'content-length'
                ]
            self._headerlist.append(('Content-Length', str(len(body))))
        elif app_iter is None and not code_has_body:
            app_iter = [b'']

        self._app_iter = app_iter

        # Loop through all the remaining keyword arguments
        for name, value in kw.items():
            if not hasattr(self.__class__, name):
                # Not a basic attribute
                raise TypeError(
                    "Unexpected keyword: %s=%r" % (name, value))
            setattr(self, name, value)

    @classmethod
    def from_file(cls, fp):
        """Reads a response from a file-like object (it must implement
        ``.read(size)`` and ``.readline()``).

        It will read up to the end of the response, not the end of the
        file.

        This reads the response as represented by ``str(resp)``; it
        may not read every valid HTTP response properly.  Responses
        must have a ``Content-Length``."""
        headerlist = []
        status = fp.readline().strip()
        is_text = isinstance(status, text_type)

        if is_text:
            _colon = ':'
            _http = 'HTTP/'
        else:
            _colon = b':'
            _http = b'HTTP/'

        if status.startswith(_http):
            (http_ver, status_num, status_text) = status.split(None, 2)
            status = '%s %s' % (native_(status_num), native_(status_text))

        while 1:
            line = fp.readline().strip()
            if not line:
                # end of headers
                break
            try:
                header_name, value = line.split(_colon, 1)
            except ValueError:
                raise ValueError('Bad header line: %r' % line)
            value = value.strip()
            headerlist.append((
                native_(header_name, 'latin-1'),
                native_(value, 'latin-1')
            ))
        r = cls(
            status=status,
            headerlist=headerlist,
            app_iter=(),
        )
        body = fp.read(r.content_length or 0)
        if is_text:
            r.text = body
        else:
            r.body = body
        return r

    def copy(self):
        """Makes a copy of the response."""
        # we need to do this for app_iter to be reusable
        app_iter = list(self._app_iter)
        iter_close(self._app_iter)
        # and this to make sure app_iter instances are different
        self._app_iter = list(app_iter)
        return self.__class__(
            status=self._status,
            headerlist=self._headerlist[:],
            app_iter=app_iter,
            conditional_response=self.conditional_response)

    #
    # __repr__, __str__
    #

    def __repr__(self):
        return '<%s at 0x%x %s>' % (self.__class__.__name__, abs(id(self)),
                                    self.status)

    def __str__(self, skip_body=False):
        parts = [self.status]
        if not skip_body:
            # Force enumeration of the body (to set content-length)
            self.body
        parts += map('%s: %s'.__mod__, self.headerlist)
        if not skip_body and self.body:
            parts += ['', self.body if PY2 else self.text]
        return '\r\n'.join(parts)

    #
    # status, status_code/status_int
    #

    def _status__get(self):
        """
        The status string.
        """
        return self._status

    def _status__set(self, value):
        try:
            code = int(value)
        except (ValueError, TypeError):
            pass
        else:
            self.status_code = code
            return
        if not PY2:
            if isinstance(value, bytes):
                value = value.decode('ascii')
        elif isinstance(value, text_type):
            value = value.encode('ascii')
        if not isinstance(value, str):
            raise TypeError(
                "You must set status to a string or integer (not %s)"
                % type(value))

        # Attempt to get the status code itself, if this fails we should fail
        try:
            # We don't need this value anywhere, we just want to validate it's
            # an integer. So we are using the side-effect of int() raises a
            # ValueError as a test
            int(value.split()[0])
        except ValueError:
            raise ValueError('Invalid status code, integer required.')
        self._status = value

    status = property(_status__get, _status__set, doc=_status__get.__doc__)

    def _status_code__get(self):
        """
        The status as an integer.
        """
        return int(self._status.split()[0])

    def _status_code__set(self, code):
        try:
            self._status = '%d %s' % (code, status_reasons[code])
        except KeyError:
            self._status = '%d %s' % (code, status_generic_reasons[code // 100])

    status_code = status_int = property(_status_code__get, _status_code__set,
                                        doc=_status_code__get.__doc__)

    #
    # headerslist, headers
    #

    def _headerlist__get(self):
        """
        The list of response headers.
        """
        return self._headerlist

    def _headerlist__set(self, value):
        self._headers = None
        if not isinstance(value, list):
            if hasattr(value, 'items'):
                value = value.items()
            value = list(value)
        self._headerlist = value

    def _headerlist__del(self):
        self.headerlist = []

    headerlist = property(_headerlist__get, _headerlist__set,
                          _headerlist__del, doc=_headerlist__get.__doc__)

    def _headers__get(self):
        """
        The headers in a dictionary-like object.
        """
        if self._headers is None:
            self._headers = ResponseHeaders.view_list(self._headerlist)
        return self._headers

    def _headers__set(self, value):
        if hasattr(value, 'items'):
            value = value.items()
        self.headerlist = value
        self._headers = None

    headers = property(_headers__get, _headers__set, doc=_headers__get.__doc__)

    #
    # body
    #

    def _body__get(self):
        """
        The body of the response, as a :class:`bytes`.  This will read in
        the entire app_iter if necessary.
        """
        app_iter = self._app_iter
#         try:
#             if len(app_iter) == 1:
#                 return app_iter[0]
#         except:
#             pass
        if isinstance(app_iter, list) and len(app_iter) == 1:
            return app_iter[0]
        if app_iter is None:
            raise AttributeError("No body has been set")
        try:
            body = b''.join(app_iter)
        finally:
            iter_close(app_iter)
        if isinstance(body, text_type):
            raise _error_unicode_in_app_iter(app_iter, body)
        self._app_iter = [body]
        if len(body) == 0:
            # if body-length is zero, we assume it's a HEAD response and
            # leave content_length alone
            pass
        elif self.content_length is None:
            self.content_length = len(body)
        elif self.content_length != len(body):
            raise AssertionError(
                "Content-Length is different from actual app_iter length "
                "(%r!=%r)"
                % (self.content_length, len(body))
            )
        return body

    def _body__set(self, value=b''):
        if not isinstance(value, bytes):
            if isinstance(value, text_type):
                msg = ("You cannot set Response.body to a text object "
                       "(use Response.text)")
            else:
                msg = ("You can only set the body to a binary type (not %s)" %
                       type(value))
            raise TypeError(msg)
        if self._app_iter is not None:
            self.content_md5 = None
        self._app_iter = [value]
        self.content_length = len(value)

#     def _body__del(self):
#         self.body = ''
#         #self.content_length = None

    body = property(_body__get, _body__set, _body__set)

    def _json_body__get(self):
        """
        Set/get the body of the response as JSON.

        .. note::

           This will automatically :meth:`~bytes.decode` the
           :attr:`~Response.body` as ``UTF-8`` on get, and
           :meth:`~str.encode` the :meth:`json.dumps` as ``UTF-8``
           before assigning to :attr:`~Response.body`.

        """
        # Note: UTF-8 is a content-type specific default for JSON
        return json.loads(self.body.decode('UTF-8'))

    def _json_body__set(self, value):
        self.body = json.dumps(value, separators=(',', ':')).encode('UTF-8')

    def _json_body__del(self):
        del self.body

    json = json_body = property(_json_body__get, _json_body__set, _json_body__del)

    def _has_body__get(self):
        """
        Determine if the the response has a :attr:`~Response.body`. In
        contrast to simply accessing :attr:`~Response.body`, this method
        will **not** read the underlying :attr:`~Response.app_iter`.
        """

        app_iter = self._app_iter

        if isinstance(app_iter, list) and len(app_iter) == 1:
            if app_iter[0] != b'':
                return True
            else:
                return False

        if app_iter is None: # pragma: no cover
            return False

        return True

    has_body = property(_has_body__get)

    #
    # text, unicode_body, ubody
    #

    def _text__get(self):
        """
        Get/set the text value of the body using the ``charset`` of the
        ``Content-Type`` or the ``default_body_encoding``.
        """
        if not self.charset and not self.default_body_encoding:
            raise AttributeError(
                "You cannot access Response.text unless charset or default_body_encoding"
                " is set"
            )
        decoding = self.charset or self.default_body_encoding
        body = self.body
        return body.decode(decoding, self.unicode_errors)

    def _text__set(self, value):
        if not self.charset and not self.default_body_encoding:
            raise AttributeError(
                "You cannot access Response.text unless charset or default_body_encoding"
                " is set"
            )
        if not isinstance(value, text_type):
            raise TypeError(
                "You can only set Response.text to a unicode string "
                "(not %s)" % type(value))
        encoding = self.charset or self.default_body_encoding
        self.body = value.encode(encoding)

    def _text__del(self):
        del self.body

    text = property(_text__get, _text__set, _text__del, doc=_text__get.__doc__)

    unicode_body = ubody = property(_text__get, _text__set, _text__del,
                                    "Deprecated alias for .text")

    #
    # body_file, write(text)
    #

    def _body_file__get(self):
        """
        A file-like object that can be used to write to the
        body.  If you passed in a list ``app_iter``, that ``app_iter`` will be
        modified by writes.
        """
        return ResponseBodyFile(self)

    def _body_file__set(self, file):
        self.app_iter = iter_file(file)

    def _body_file__del(self):
        del self.body

    body_file = property(_body_file__get, _body_file__set, _body_file__del,
                         doc=_body_file__get.__doc__)

    def write(self, text):
        if not isinstance(text, bytes):
            if not isinstance(text, text_type):
                msg = "You can only write str to a Response.body_file, not %s"
                raise TypeError(msg % type(text))
            if not self.charset:
                msg = ("You can only write text to Response if charset has "
                       "been set")
                raise TypeError(msg)
            text = text.encode(self.charset)
        app_iter = self._app_iter
        if not isinstance(app_iter, list):
            try:
                new_app_iter = self._app_iter = list(app_iter)
            finally:
                iter_close(app_iter)
            app_iter = new_app_iter
            self.content_length = sum(len(chunk) for chunk in app_iter)
        app_iter.append(text)
        if self.content_length is not None:
            self.content_length += len(text)

    #
    # app_iter
    #

    def _app_iter__get(self):
        """
        Returns the ``app_iter`` of the response.

        If ``body`` was set, this will create an ``app_iter`` from that
        ``body`` (a single-item list).
        """
        return self._app_iter

    def _app_iter__set(self, value):
        if self._app_iter is not None:
            # Undo the automatically-set content-length
            self.content_length = None
        self._app_iter = value

    def _app_iter__del(self):
        self._app_iter = []
        self.content_length = None

    app_iter = property(_app_iter__get, _app_iter__set, _app_iter__del,
                        doc=_app_iter__get.__doc__)

    #
    # headers attrs
    #

    allow = list_header('Allow', '14.7')
    # TODO: (maybe) support response.vary += 'something'
    # TODO: same thing for all listy headers
    vary = list_header('Vary', '14.44')

    content_length = converter(
        header_getter('Content-Length', '14.17'),
        parse_int, serialize_int, 'int')

    content_encoding = header_getter('Content-Encoding', '14.11')
    content_language = list_header('Content-Language', '14.12')
    content_location = header_getter('Content-Location', '14.14')
    content_md5 = header_getter('Content-MD5', '14.14')
    content_disposition = header_getter('Content-Disposition', '19.5.1')

    accept_ranges = header_getter('Accept-Ranges', '14.5')
    content_range = converter(
        header_getter('Content-Range', '14.16'),
        parse_content_range, serialize_content_range, 'ContentRange object')

    date = date_header('Date', '14.18')
    expires = date_header('Expires', '14.21')
    last_modified = date_header('Last-Modified', '14.29')

    _etag_raw = header_getter('ETag', '14.19')
    etag = converter(
        _etag_raw,
        parse_etag_response, serialize_etag_response,
        'Entity tag'
    )
    @property
    def etag_strong(self):
        return parse_etag_response(self._etag_raw, strong=True)

    location = header_getter('Location', '14.30')
    pragma = header_getter('Pragma', '14.32')
    age = converter(
        header_getter('Age', '14.6'),
        parse_int_safe, serialize_int, 'int')

    retry_after = converter(
        header_getter('Retry-After', '14.37'),
        parse_date_delta, serialize_date_delta, 'HTTP date or delta seconds')

    server = header_getter('Server', '14.38')

    # TODO: the standard allows this to be a list of challenges
    www_authenticate = converter(
        header_getter('WWW-Authenticate', '14.47'),
        parse_auth, serialize_auth,
    )

    #
    # charset
    #

    def _charset__get(self):
        """
        Get/set the ``charset`` specified in ``Content-Type``.

        There is no checking to validate that a ``content_type`` actually
        allows for a ``charset`` parameter.
        """
        header = self.headers.get('Content-Type')
        if not header:
            return None
        match = CHARSET_RE.search(header)
        if match:
            return match.group(1)
        return None

    def _charset__set(self, charset):
        if charset is None:
            self._charset__del()
            return
        header = self.headers.get('Content-Type', None)
        if header is None:
            raise AttributeError("You cannot set the charset when no "
                                 "content-type is defined")
        match = CHARSET_RE.search(header)
        if match:
            header = header[:match.start()] + header[match.end():]
        header += '; charset=%s' % charset
        self.headers['Content-Type'] = header

    def _charset__del(self):
        header = self.headers.pop('Content-Type', None)
        if header is None:
            # Don't need to remove anything
            return
        match = CHARSET_RE.search(header)
        if match:
            header = header[:match.start()] + header[match.end():]
        self.headers['Content-Type'] = header

    charset = property(_charset__get, _charset__set, _charset__del,
                       doc=_charset__get.__doc__)

    #
    # content_type
    #

    def _content_type__get(self):
        """
        Get/set the ``Content-Type`` header. If no ``Content-Type`` header is
        set, this will return ``None``.

        .. versionchanged:: 1.7

            Setting a new ``Content-Type`` will remove all ``Content-Type``
            parameters and reset the ``charset`` to the default if the
            ``Content-Type`` is ``text/*`` or XML (``application/xml`` or
            ``*/*+xml``).

            To preserve all ``Content-Type`` parameters, you may use the
            following code:

            .. code-block:: python

                resp = Response()
                params = resp.content_type_params
                resp.content_type = 'application/something'
                resp.content_type_params = params
        """
        header = self.headers.get('Content-Type')
        if not header:
            return None
        return header.split(';', 1)[0]

    def _content_type__set(self, value):
        if not value:
            self._content_type__del()
            return
        else:
            content_type = value

            # Set up the charset if the content-type doesn't have one

            has_charset = 'charset=' in content_type

            new_charset = None

            if (
                not has_charset and
                self.default_charset
            ):
                new_charset = self.default_charset

            # Optimize for the default_content_type as shipped by
            # WebOb, becuase we know that 'text/html' has a charset,
            # otherwise add a charset if the content_type has a charset.
            #
            # We add the default charset if the content-type is "texty".
            if (
                new_charset and
                (
                    content_type == 'text/html' or
                    _content_type_has_charset(content_type)
                )
            ):
                content_type += '; charset=' + new_charset

            self.headers['Content-Type'] = content_type

    def _content_type__del(self):
        self.headers.pop('Content-Type', None)

    content_type = property(_content_type__get, _content_type__set,
                            _content_type__del, doc=_content_type__get.__doc__)

    #
    # content_type_params
    #

    def _content_type_params__get(self):
        """
        A dictionary of all the parameters in the content type.

        (This is not a view, set to change, modifications of the dict will not
        be applied otherwise.)
        """
        params = self.headers.get('Content-Type', '')
        if ';' not in params:
            return {}
        params = params.split(';', 1)[1]
        result = {}
        for match in _PARAM_RE.finditer(params):
            result[match.group(1)] = match.group(2) or match.group(3) or ''
        return result

    def _content_type_params__set(self, value_dict):
        if not value_dict:
            self._content_type_params__del()
            return

        params = []
        for k, v in sorted(value_dict.items()):
            if not _OK_PARAM_RE.search(v):
                v = '"%s"' % v.replace('"', '\\"')
            params.append('; %s=%s' % (k, v))
        ct = self.headers.pop('Content-Type', '').split(';', 1)[0]
        ct += ''.join(params)
        self.headers['Content-Type'] = ct

    def _content_type_params__del(self):
        self.headers['Content-Type'] = self.headers.get(
            'Content-Type', '').split(';', 1)[0]

    content_type_params = property(
        _content_type_params__get,
        _content_type_params__set,
        _content_type_params__del,
        _content_type_params__get.__doc__
    )

    #
    # set_cookie, unset_cookie, delete_cookie, merge_cookies
    #

    def set_cookie(self, name, value='', max_age=None,
                   path='/', domain=None, secure=False, httponly=False,
                   comment=None, expires=None, overwrite=False,
                   samesite=None):
        """
        Set (add) a cookie for the response.

        Arguments are:

        ``name``

           The cookie name.

        ``value``

           The cookie value, which should be a string or ``None``.  If
           ``value`` is ``None``, it's equivalent to calling the
           :meth:`webob.response.Response.unset_cookie` method for this
           cookie key (it effectively deletes the cookie on the client).

        ``max_age``

           An integer representing a number of seconds, ``datetime.timedelta``,
           or ``None``. This value is used as the ``Max-Age`` of the generated
           cookie.  If ``expires`` is not passed and this value is not
           ``None``, the ``max_age`` value will also influence the ``Expires``
           value of the cookie (``Expires`` will be set to ``now`` +
           ``max_age``).  If this value is ``None``, the cookie will not have a
           ``Max-Age`` value (unless ``expires`` is set). If both ``max_age``
           and ``expires`` are set, this value takes precedence.

        ``path``

           A string representing the cookie ``Path`` value.  It defaults to
           ``/``.

        ``domain``

           A string representing the cookie ``Domain``, or ``None``.  If
           domain is ``None``, no ``Domain`` value will be sent in the
           cookie.

        ``secure``

           A boolean.  If it's ``True``, the ``secure`` flag will be sent in
           the cookie, if it's ``False``, the ``secure`` flag will not be
           sent in the cookie.

        ``httponly``

           A boolean.  If it's ``True``, the ``HttpOnly`` flag will be sent
           in the cookie, if it's ``False``, the ``HttpOnly`` flag will not
           be sent in the cookie.

        ``samesite``

          A string representing the ``SameSite`` attribute of the cookie or
          ``None``. If samesite is ``None`` no ``SameSite`` value will be sent
          in the cookie. Should only be ``"Strict"`` or ``"Lax"``.

        ``comment``

           A string representing the cookie ``Comment`` value, or ``None``.
           If ``comment`` is ``None``, no ``Comment`` value will be sent in
           the cookie.

        ``expires``

           A ``datetime.timedelta`` object representing an amount of time,
           ``datetime.datetime`` or ``None``. A non-``None`` value is used to
           generate the ``Expires`` value of the generated cookie. If
           ``max_age`` is not passed, but this value is not ``None``, it will
           influence the ``Max-Age`` header. If this value is ``None``, the
           ``Expires`` cookie value will be unset (unless ``max_age`` is set).
           If ``max_age`` is set, it will be used to generate the ``expires``
           and this value is ignored.

           If a ``datetime.datetime`` is provided it has to either be timezone
           aware or be based on UTC. ``datetime.datetime`` objects that are
           local time are not supported. Timezone aware ``datetime.datetime``
           objects are converted to UTC.

           This argument will be removed in future versions of WebOb (version
           1.9).

        ``overwrite``

           If this key is ``True``, before setting the cookie, unset any
           existing cookie.

        """

        # Remove in WebOb 1.10
        if expires:
            warn_deprecation('Argument "expires" will be removed in a future '
                             'version of WebOb, please use "max_age".', 1.10, 1)

        if overwrite:
            self.unset_cookie(name, strict=False)

        # If expires is set, but not max_age we set max_age to expires
        if not max_age and isinstance(expires, timedelta):
            max_age = expires

        # expires can also be a datetime
        if not max_age and isinstance(expires, datetime):

            # If expires has a timezone attached, convert it to UTC
            if expires.tzinfo and expires.utcoffset():
                expires = (expires - expires.utcoffset()).replace(tzinfo=None)

            max_age = expires - datetime.utcnow()

        value = bytes_(value, 'utf-8')

        cookie = make_cookie(name, value, max_age=max_age, path=path,
                domain=domain, secure=secure, httponly=httponly,
                comment=comment, samesite=samesite)
        self.headerlist.append(('Set-Cookie', cookie))

    def delete_cookie(self, name, path='/', domain=None):
        """
        Delete a cookie from the client.  Note that ``path`` and ``domain``
        must match how the cookie was originally set.

        This sets the cookie to the empty string, and ``max_age=0`` so
        that it should expire immediately.
        """
        self.set_cookie(name, None, path=path, domain=domain)

    def unset_cookie(self, name, strict=True):
        """
        Unset a cookie with the given name (remove it from the response).
        """
        existing = self.headers.getall('Set-Cookie')
        if not existing and not strict:
            return
        cookies = Cookie()
        for header in existing:
            cookies.load(header)
        if isinstance(name, text_type):
            name = name.encode('utf8')
        if name in cookies:
            del cookies[name]
            del self.headers['Set-Cookie']
            for m in cookies.values():
                self.headerlist.append(('Set-Cookie', m.serialize()))
        elif strict:
            raise KeyError("No cookie has been set with the name %r" % name)

    def merge_cookies(self, resp):
        """Merge the cookies that were set on this response with the
        given ``resp`` object (which can be any WSGI application).

        If the ``resp`` is a :class:`webob.Response` object, then the
        other object will be modified in-place.
        """
        if not self.headers.get('Set-Cookie'):
            return resp
        if isinstance(resp, Response):
            for header in self.headers.getall('Set-Cookie'):
                resp.headers.add('Set-Cookie', header)
            return resp
        else:
            c_headers = [h for h in self.headerlist if
                         h[0].lower() == 'set-cookie']
            def repl_app(environ, start_response):
                def repl_start_response(status, headers, exc_info=None):
                    return start_response(status, headers + c_headers,
                                          exc_info=exc_info)
                return resp(environ, repl_start_response)
            return repl_app

    #
    # cache_control
    #

    _cache_control_obj = None

    def _cache_control__get(self):
        """
        Get/set/modify the Cache-Control header (`HTTP spec section 14.9
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.9>`_).
        """
        value = self.headers.get('cache-control', '')
        if self._cache_control_obj is None:
            self._cache_control_obj = CacheControl.parse(
                value, updates_to=self._update_cache_control, type='response')
            self._cache_control_obj.header_value = value
        if self._cache_control_obj.header_value != value:
            new_obj = CacheControl.parse(value, type='response')
            self._cache_control_obj.properties.clear()
            self._cache_control_obj.properties.update(new_obj.properties)
            self._cache_control_obj.header_value = value
        return self._cache_control_obj

    def _cache_control__set(self, value):
        # This actually becomes a copy
        if not value:
            value = ""
        if isinstance(value, dict):
            value = CacheControl(value, 'response')
        if isinstance(value, text_type):
            value = str(value)
        if isinstance(value, str):
            if self._cache_control_obj is None:
                self.headers['Cache-Control'] = value
                return
            value = CacheControl.parse(value, 'response')
        cache = self.cache_control
        cache.properties.clear()
        cache.properties.update(value.properties)

    def _cache_control__del(self):
        self.cache_control = {}

    def _update_cache_control(self, prop_dict):
        value = serialize_cache_control(prop_dict)
        if not value:
            if 'Cache-Control' in self.headers:
                del self.headers['Cache-Control']
        else:
            self.headers['Cache-Control'] = value

    cache_control = property(
        _cache_control__get, _cache_control__set,
        _cache_control__del, doc=_cache_control__get.__doc__)

    #
    # cache_expires
    #

    def _cache_expires(self, seconds=0, **kw):
        """
            Set expiration on this request.  This sets the response to
            expire in the given seconds, and any other attributes are used
            for ``cache_control`` (e.g., ``private=True``).
        """
        if seconds is True:
            seconds = 0
        elif isinstance(seconds, timedelta):
            seconds = timedelta_to_seconds(seconds)
        cache_control = self.cache_control
        if seconds is None:
            pass
        elif not seconds:
            # To really expire something, you have to force a
            # bunch of these cache control attributes, and IE may
            # not pay attention to those still so we also set
            # Expires.
            cache_control.no_store = True
            cache_control.no_cache = True
            cache_control.must_revalidate = True
            cache_control.max_age = 0
            cache_control.post_check = 0
            cache_control.pre_check = 0
            self.expires = datetime.utcnow()
            if 'last-modified' not in self.headers:
                self.last_modified = datetime.utcnow()
            self.pragma = 'no-cache'
        else:
            cache_control.properties.clear()
            cache_control.max_age = seconds
            self.expires = datetime.utcnow() + timedelta(seconds=seconds)
            self.pragma = None
        for name, value in kw.items():
            setattr(cache_control, name, value)

    cache_expires = property(lambda self: self._cache_expires, _cache_expires)

    #
    # encode_content, decode_content, md5_etag
    #

    def encode_content(self, encoding='gzip', lazy=False):
        """
        Encode the content with the given encoding (only ``gzip`` and
        ``identity`` are supported).
        """
        assert encoding in ('identity', 'gzip'), \
            "Unknown encoding: %r" % encoding
        if encoding == 'identity':
            self.decode_content()
            return
        if self.content_encoding == 'gzip':
            return
        if lazy:
            self.app_iter = gzip_app_iter(self._app_iter)
            self.content_length = None
        else:
            self.app_iter = list(gzip_app_iter(self._app_iter))
            self.content_length = sum(map(len, self._app_iter))
        self.content_encoding = 'gzip'

    def decode_content(self):
        content_encoding = self.content_encoding or 'identity'
        if content_encoding == 'identity':
            return
        if content_encoding not in ('gzip', 'deflate'):
            raise ValueError(
                "I don't know how to decode the content %s" % content_encoding)
        if content_encoding == 'gzip':
            from gzip import GzipFile
            from io import BytesIO
            gzip_f = GzipFile(filename='', mode='r', fileobj=BytesIO(self.body))
            self.body = gzip_f.read()
            self.content_encoding = None
            gzip_f.close()
        else:
            # Weird feature: http://bugs.python.org/issue5784
            self.body = zlib.decompress(self.body, -15)
            self.content_encoding = None

    def md5_etag(self, body=None, set_content_md5=False):
        """
        Generate an etag for the response object using an MD5 hash of
        the body (the ``body`` parameter, or ``self.body`` if not given).

        Sets ``self.etag``.

        If ``set_content_md5`` is ``True``, sets ``self.content_md5`` as well.
        """
        if body is None:
            body = self.body
        md5_digest = md5(body).digest()
        md5_digest = b64encode(md5_digest)
        md5_digest = md5_digest.replace(b'\n', b'')
        md5_digest = native_(md5_digest)
        self.etag = md5_digest.strip('=')
        if set_content_md5:
            self.content_md5 = md5_digest

    @staticmethod
    def _make_location_absolute(environ, value):
        if SCHEME_RE.search(value):
            return value

        new_location = urlparse.urljoin(_request_uri(environ), value)
        return new_location

    def _abs_headerlist(self, environ):
        # Build the headerlist, if we have a Location header, make it absolute
        return [
            (k, v) if k.lower() != 'location'
            else (k, self._make_location_absolute(environ, v))
            for (k, v)
            in self._headerlist
        ]

    #
    # __call__, conditional_response_app
    #

    def __call__(self, environ, start_response):
        """
        WSGI application interface
        """
        if self.conditional_response:
            return self.conditional_response_app(environ, start_response)

        headerlist = self._abs_headerlist(environ)

        start_response(self.status, headerlist)
        if environ['REQUEST_METHOD'] == 'HEAD':
            # Special case here...
            return EmptyResponse(self._app_iter)
        return self._app_iter

    _safe_methods = ('GET', 'HEAD')

    def conditional_response_app(self, environ, start_response):
        """
        Like the normal ``__call__`` interface, but checks conditional headers:

            * ``If-Modified-Since``   (``304 Not Modified``; only on ``GET``,
              ``HEAD``)
            * ``If-None-Match``       (``304 Not Modified``; only on ``GET``,
              ``HEAD``)
            * ``Range``               (``406 Partial Content``; only on ``GET``,
              ``HEAD``)
        """
        req = BaseRequest(environ)

        headerlist = self._abs_headerlist(environ)

        method = environ.get('REQUEST_METHOD', 'GET')
        if method in self._safe_methods:
            status304 = False
            if req.if_none_match and self.etag:
                status304 = self.etag in req.if_none_match
            elif req.if_modified_since and self.last_modified:
                status304 = self.last_modified <= req.if_modified_since
            if status304:
                start_response('304 Not Modified', filter_headers(headerlist))
                return EmptyResponse(self._app_iter)
        if (
            req.range and self in req.if_range and
            self.content_range is None and
            method in ('HEAD', 'GET') and
            self.status_code == 200 and
            self.content_length is not None
        ):
            content_range = req.range.content_range(self.content_length)
            if content_range is None:
                iter_close(self._app_iter)
                body = bytes_("Requested range not satisfiable: %s" % req.range)
                headerlist = [
                    ('Content-Length', str(len(body))),
                    ('Content-Range', str(ContentRange(None, None,
                                                       self.content_length))),
                    ('Content-Type', 'text/plain'),
                ] + filter_headers(headerlist)
                start_response('416 Requested Range Not Satisfiable',
                               headerlist)
                if method == 'HEAD':
                    return ()
                return [body]
            else:
                app_iter = self.app_iter_range(content_range.start,
                                               content_range.stop)
                if app_iter is not None:
                    # the following should be guaranteed by
                    # Range.range_for_length(length)
                    assert content_range.start is not None
                    headerlist = [
                        ('Content-Length',
                         str(content_range.stop - content_range.start)),
                        ('Content-Range', str(content_range)),
                    ] + filter_headers(headerlist, ('content-length',))
                    start_response('206 Partial Content', headerlist)
                    if method == 'HEAD':
                        return EmptyResponse(app_iter)
                    return app_iter

        start_response(self.status, headerlist)
        if method == 'HEAD':
            return EmptyResponse(self._app_iter)
        return self._app_iter

    def app_iter_range(self, start, stop):
        """
        Return a new ``app_iter`` built from the response ``app_iter``, that
        serves up only the given ``start:stop`` range.
        """
        app_iter = self._app_iter
        if hasattr(app_iter, 'app_iter_range'):
            return app_iter.app_iter_range(start, stop)
        return AppIterRange(app_iter, start, stop)


def filter_headers(hlist, remove_headers=('content-length', 'content-type')):
    return [h for h in hlist if (h[0].lower() not in remove_headers)]


def iter_file(file, block_size=1 << 18): # 256Kb
    while True:
        data = file.read(block_size)
        if not data:
            break
        yield data

class ResponseBodyFile(object):
    mode = 'wb'
    closed = False

    def __init__(self, response):
        """
        Represents a :class:`~Response` as a file like object.
        """
        self.response = response
        self.write = response.write

    def __repr__(self):
        return '<body_file for %r>' % self.response

    encoding = property(
        lambda self: self.response.charset,
        doc="The encoding of the file (inherited from response.charset)"
    )

    def writelines(self, seq):
        """
        Write a sequence of lines to the response.
        """
        for item in seq:
            self.write(item)

    def close(self):
        raise NotImplementedError("Response bodies cannot be closed")

    def flush(self):
        pass

    def tell(self):
        """
        Provide the current location where we are going to start writing.
        """
        if not self.response.has_body:
            return 0

        return sum([len(chunk) for chunk in self.response.app_iter])


class AppIterRange(object):
    """
    Wraps an ``app_iter``, returning just a range of bytes.
    """

    def __init__(self, app_iter, start, stop):
        assert start >= 0, "Bad start: %r" % start
        assert stop is None or (stop >= 0 and stop >= start), (
            "Bad stop: %r" % stop)
        self.app_iter = iter(app_iter)
        self._pos = 0 # position in app_iter
        self.start = start
        self.stop = stop

    def __iter__(self):
        return self

    def _skip_start(self):
        start, stop = self.start, self.stop
        for chunk in self.app_iter:
            self._pos += len(chunk)
            if self._pos < start:
                continue
            elif self._pos == start:
                return b''
            else:
                chunk = chunk[start - self._pos:]
                if stop is not None and self._pos > stop:
                    chunk = chunk[:stop - self._pos]
                    assert len(chunk) == stop - start
                return chunk
        else:
            raise StopIteration()

    def next(self):
        if self._pos < self.start:
            # need to skip some leading bytes
            return self._skip_start()
        stop = self.stop
        if stop is not None and self._pos >= stop:
            raise StopIteration

        chunk = next(self.app_iter)
        self._pos += len(chunk)

        if stop is None or self._pos <= stop:
            return chunk
        else:
            return chunk[:stop - self._pos]

    __next__ = next # py3

    def close(self):
        iter_close(self.app_iter)


class EmptyResponse(object):
    """
    An empty WSGI response.

    An iterator that immediately stops. Optionally provides a close
    method to close an underlying ``app_iter`` it replaces.
    """

    def __init__(self, app_iter=None):
        if app_iter is not None and hasattr(app_iter, 'close'):
            self.close = app_iter.close

    def __iter__(self):
        return self

    def __len__(self):
        return 0

    def next(self):
        raise StopIteration()

    __next__ = next # py3

def _is_xml(content_type):
    return (
        content_type.startswith('application/xml') or
        (
            content_type.startswith('application/') and
            content_type.endswith('+xml')
        ) or
        (
            content_type.startswith('image/') and
            content_type.endswith('+xml')
        )
    )

def _content_type_has_charset(content_type):
    return (
        content_type.startswith('text/') or
        _is_xml(content_type)
    )

def _request_uri(environ):
    """Like ``wsgiref.url.request_uri``, except eliminates ``:80`` ports.

    Returns the full request URI."""
    url = environ['wsgi.url_scheme'] + '://'

    if environ.get('HTTP_HOST'):
        url += environ['HTTP_HOST']
    else:
        url += environ['SERVER_NAME'] + ':' + environ['SERVER_PORT']
    if url.endswith(':80') and environ['wsgi.url_scheme'] == 'http':
        url = url[:-3]
    elif url.endswith(':443') and environ['wsgi.url_scheme'] == 'https':
        url = url[:-4]

    if PY2:
        script_name = environ.get('SCRIPT_NAME', '/')
        path_info = environ.get('PATH_INFO', '')
    else:
        script_name = bytes_(environ.get('SCRIPT_NAME', '/'), 'latin-1')
        path_info = bytes_(environ.get('PATH_INFO', ''), 'latin-1')

    url += url_quote(script_name)
    qpath_info = url_quote(path_info)
    if 'SCRIPT_NAME' not in environ:
        url += qpath_info[1:]
    else:
        url += qpath_info
    return url


def iter_close(iter):
    if hasattr(iter, 'close'):
        iter.close()

def gzip_app_iter(app_iter):
    size = 0
    crc = zlib.crc32(b"") & 0xffffffff
    compress = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS,
                                zlib.DEF_MEM_LEVEL, 0)

    yield _gzip_header
    for item in app_iter:
        size += len(item)
        crc = zlib.crc32(item, crc) & 0xffffffff

        # The compress function may return zero length bytes if the input is
        # small enough; it buffers the input for the next iteration or for a
        # flush.
        result = compress.compress(item)
        if result:
            yield result

    # Similarly, flush may also not yield a value.
    result = compress.flush()
    if result:
        yield result
    yield struct.pack("<2L", crc, size & 0xffffffff)

def _error_unicode_in_app_iter(app_iter, body):
    app_iter_repr = repr(app_iter)
    if len(app_iter_repr) > 50:
        app_iter_repr = (
            app_iter_repr[:30] + '...' + app_iter_repr[-10:])
    raise TypeError(
        'An item of the app_iter (%s) was text, causing a '
        'text body: %r' % (app_iter_repr, body))
