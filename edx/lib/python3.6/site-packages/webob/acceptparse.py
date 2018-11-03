"""
Parse four ``Accept*`` headers used in server-driven content negotiation.

The four headers are ``Accept``, ``Accept-Charset``, ``Accept-Encoding`` and
``Accept-Language``.
"""

from collections import namedtuple
import re
import textwrap
import warnings


# RFC 7230 Section 3.2.3 "Whitespace"
# OWS            = *( SP / HTAB )
#                ; optional whitespace
OWS_re = '[ \t]*'

# RFC 7230 Section 3.2.6 "Field Value Components":
# tchar          = "!" / "#" / "$" / "%" / "&" / "'" / "*"
#                / "+" / "-" / "." / "^" / "_" / "`" / "|" / "~"
#                / DIGIT / ALPHA
tchar_re = r"[!#$%&'*+\-.^_`|~0-9A-Za-z]"

# token          = 1*tchar
token_re = tchar_re + '+'
token_compiled_re = re.compile('^' + token_re + '$')

# RFC 7231 Section 5.3.1 "Quality Values"
# qvalue = ( "0" [ "." 0*3DIGIT ] )
#        / ( "1" [ "." 0*3("0") ] )
qvalue_re = (
    r'(?:0(?:\.[0-9]{0,3})?)'
    '|'
    r'(?:1(?:\.0{0,3})?)'
)
# weight = OWS ";" OWS "q=" qvalue
weight_re = OWS_re + ';' + OWS_re + '[qQ]=(' + qvalue_re + ')'


def _item_n_weight_re(item_re):
    return '(' + item_re + ')(?:' + weight_re + ')?'


def _item_qvalue_pair_to_header_element(pair):
    item, qvalue = pair
    if qvalue == 1.0:
        element = item
    elif qvalue == 0.0:
        element = '{};q=0'.format(item)
    else:
        element = '{};q={}'.format(item, qvalue)
    return element


def _list_0_or_more__compiled_re(element_re):
    # RFC 7230 Section 7 "ABNF List Extension: #rule":
    # #element => [ ( "," / element ) *( OWS "," [ OWS element ] ) ]
    return re.compile(
        '^(?:$)|' +
        '(?:' +
        '(?:,|(?:' + element_re + '))' +
        '(?:' + OWS_re + ',(?:' + OWS_re + element_re + ')?)*' +
        ')$',
    )


def _list_1_or_more__compiled_re(element_re):
    # RFC 7230 Section 7 "ABNF List Extension: #rule":
    # 1#element => *( "," OWS ) element *( OWS "," [ OWS element ] )
    # and RFC 7230 Errata ID: 4169
    return re.compile(
        '^(?:,' + OWS_re + ')*' + element_re +
        '(?:' + OWS_re + ',(?:' + OWS_re + element_re + ')?)*$',
    )


class AcceptOffer(namedtuple('AcceptOffer', ['type', 'subtype', 'params'])):
    """
    A pre-parsed offer tuple represeting a value in the format
    ``type/subtype;param0=value0;param1=value1``.

    :ivar type: The media type's root category.
    :ivar subtype: The media type's subtype.
    :ivar params: A tuple of 2-tuples containing parameter names and values.

    """
    __slots__ = ()

    def __str__(self):
        """
        Return the properly quoted media type string.

        """
        value = self.type + '/' + self.subtype
        return Accept._form_media_range(value, self.params)


class Accept(object):
    """
    Represent an ``Accept`` header.

    Base class for :class:`AcceptValidHeader`, :class:`AcceptNoHeader`, and
    :class:`AcceptInvalidHeader`.
    """

    # RFC 6838 describes syntax rules for media types that are different to
    # (and stricter than) those in RFC 7231, but if RFC 7231 intended us to
    # follow the rules in RFC 6838 for media ranges, it would not have
    # specified its own syntax rules for media ranges, so it appears we should
    # use the rules in RFC 7231 for now.

    # RFC 5234 Appendix B.1 "Core Rules":
    # VCHAR         =  %x21-7E
    #                       ; visible (printing) characters
    vchar_re = '\x21-\x7e'
    # RFC 7230 Section 3.2.6 "Field Value Components":
    # quoted-string = DQUOTE *( qdtext / quoted-pair ) DQUOTE
    # qdtext        = HTAB / SP /%x21 / %x23-5B / %x5D-7E / obs-text
    # obs-text      = %x80-FF
    # quoted-pair   = "\" ( HTAB / SP / VCHAR / obs-text )
    obs_text_re = '\x80-\xff'
    qdtext_re = '[\t \x21\x23-\x5b\\\x5d-\x7e' + obs_text_re + ']'
    # The '\\' between \x5b and \x5d is needed to escape \x5d (']')
    quoted_pair_re = r'\\' + '[\t ' + vchar_re + obs_text_re + ']'
    quoted_string_re = \
        '"(?:(?:' + qdtext_re + ')|(?:' + quoted_pair_re + '))*"'

    # RFC 7231 Section 3.1.1.1 "Media Type":
    # type       = token
    # subtype    = token
    # parameter  = token "=" ( token / quoted-string )
    type_re = token_re
    subtype_re = token_re
    parameter_re = token_re + '=' + \
        '(?:(?:' + token_re + ')|(?:' + quoted_string_re + '))'

    # Section 5.3.2 "Accept":
    # media-range    = ( "*/*"
    #                  / ( type "/" "*" )
    #                  / ( type "/" subtype )
    #                  ) *( OWS ";" OWS parameter )
    media_range_re = (
        '(' +
        '(?:' + type_re + '/' + subtype_re + ')' +
        # '*' is included through type_re and subtype_re, so this covers */*
        # and type/*
        ')' +
        '(' +
        '(?:' + OWS_re + ';' + OWS_re +
        '(?![qQ]=)' +  # media type parameter cannot be named "q"
        parameter_re + ')*' +
        ')'
    )
    # accept-params  = weight *( accept-ext )
    # accept-ext = OWS ";" OWS token [ "=" ( token / quoted-string ) ]
    accept_ext_re = (
        OWS_re + ';' + OWS_re + token_re + '(?:' +
        '=(?:' +
        '(?:' + token_re + ')|(?:' + quoted_string_re + ')' +
        ')' +
        ')?'
    )
    accept_params_re = weight_re + '((?:' + accept_ext_re + ')*)'

    media_range_n_accept_params_re = media_range_re + '(?:' + \
        accept_params_re + ')?'
    media_range_n_accept_params_compiled_re = re.compile(
        media_range_n_accept_params_re,
    )

    accept_compiled_re = _list_0_or_more__compiled_re(
        element_re=media_range_n_accept_params_re,
    )

    # For parsing repeated groups within the media type parameters and
    # extension parameters segments
    parameters_compiled_re = re.compile(
        OWS_re + ';' + OWS_re + '(' + token_re + ')=(' + token_re + '|' +
        quoted_string_re + ')',
    )
    accept_ext_compiled_re = re.compile(
        OWS_re + ';' + OWS_re + '(' + token_re + ')' +
        '(?:' +
        '=(' +
        '(?:' +
        '(?:' + token_re + ')|(?:' + quoted_string_re + ')' +
        ')' +
        ')' +
        ')?',
    )

    # For parsing the media types in the `offers` argument to
    # .acceptable_offers(), we re-use the media range regex for media types.
    # This is not intended to be a validation of the offers; its main purpose
    # is to extract the media type and any media type parameters.
    media_type_re = media_range_re
    media_type_compiled_re = re.compile('^' + media_type_re + '$')

    @classmethod
    def _escape_and_quote_parameter_value(cls, param_value):
        """
        Escape and quote parameter value where necessary.

        For media type and extension parameter values.
        """
        if param_value == '':
            param_value = '""'
        else:
            param_value = param_value.replace('\\', '\\\\').replace(
                '"', r'\"',
            )
            if not token_compiled_re.match(param_value):
                param_value = '"' + param_value + '"'
        return param_value

    @classmethod
    def _form_extension_params_segment(cls, extension_params):
        """
        Convert iterable of extension parameters to str segment for header.

        `extension_params` is an iterable where each item is either a parameter
        string or a (name, value) tuple.
        """
        extension_params_segment = ''
        for item in extension_params:
            try:
                extension_params_segment += (';' + item)
            except TypeError:
                param_name, param_value = item
                param_value = cls._escape_and_quote_parameter_value(
                    param_value=param_value,
                )
                extension_params_segment += (
                    ';' + param_name + '=' + param_value
                )
        return extension_params_segment

    @classmethod
    def _form_media_range(cls, type_subtype, media_type_params):
        """
        Combine `type_subtype` and `media_type_params` to form a media range.

        `type_subtype` is a ``str``, and `media_type_params` is an iterable of
        (parameter name, parameter value) tuples.
        """
        media_type_params_segment = ''
        for param_name, param_value in media_type_params:
            param_value = cls._escape_and_quote_parameter_value(
                param_value=param_value,
            )
            media_type_params_segment += (';' + param_name + '=' + param_value)
        return type_subtype + media_type_params_segment

    @classmethod
    def _iterable_to_header_element(cls, iterable):
        """
        Convert iterable of tuples into header element ``str``.

        Each tuple is expected to be in one of two forms: (media_range, qvalue,
        extension_params_segment), or (media_range, qvalue).
        """
        try:
            media_range, qvalue, extension_params_segment = iterable
        except ValueError:
            media_range, qvalue = iterable
            extension_params_segment = ''

        if qvalue == 1.0:
            if extension_params_segment:
                element = '{};q=1{}'.format(
                    media_range, extension_params_segment,
                )
            else:
                element = media_range
        elif qvalue == 0.0:
            element = '{};q=0{}'.format(media_range, extension_params_segment)
        else:
            element = '{};q={}{}'.format(
                media_range, qvalue, extension_params_segment,
            )
        return element

    @classmethod
    def _parse_media_type_params(cls, media_type_params_segment):
        """
        Parse media type parameters segment into list of (name, value) tuples.
        """
        media_type_params = cls.parameters_compiled_re.findall(
            media_type_params_segment,
        )
        for index, (name, value) in enumerate(media_type_params):
            if value.startswith('"') and value.endswith('"'):
                value = cls._process_quoted_string_token(token=value)
                media_type_params[index] = (name, value)
        return media_type_params

    @classmethod
    def _process_quoted_string_token(cls, token):
        """
        Return unescaped and unquoted value from quoted token.
        """
        # RFC 7230, section 3.2.6 "Field Value Components": "Recipients that
        # process the value of a quoted-string MUST handle a quoted-pair as if
        # it were replaced by the octet following the backslash."
        return re.sub(r'\\(?![\\])', '', token[1:-1]).replace('\\\\', '\\')

    @classmethod
    def _python_value_to_header_str(cls, value):
        """
        Convert Python value to header string for __add__/__radd__.
        """
        if isinstance(value, str):
            return value
        if hasattr(value, 'items'):
            if value == {}:
                value = []
            else:
                value_list = []
                for media_range, item in value.items():
                    # item is either (media range, (qvalue, extension
                    # parameters segment)), or (media range, qvalue) (supported
                    # for backward compatibility)
                    if isinstance(item, (float, int)):
                        value_list.append((media_range, item, ''))
                    else:
                        value_list.append((media_range, item[0], item[1]))
                value = sorted(
                    value_list,
                    key=lambda item: item[1],  # qvalue
                    reverse=True,
                )
        if isinstance(value, (tuple, list)):
            header_elements = []
            for item in value:
                if isinstance(item, (tuple, list)):
                    item = cls._iterable_to_header_element(iterable=item)
                header_elements.append(item)
            header_str = ', '.join(header_elements)
        else:
            header_str = str(value)
        return header_str

    @classmethod
    def parse(cls, value):
        """
        Parse an ``Accept`` header.

        :param value: (``str``) header value
        :return: If `value` is a valid ``Accept`` header, returns an iterator
                 of (*media_range*, *qvalue*, *media_type_params*,
                 *extension_params*) tuples, as parsed from the header from
                 left to right.

                 | *media_range* is the media range, including any media type
                   parameters. The media range is returned in a canonicalised
                   form (except the case of the characters are unchanged):
                   unnecessary spaces around the semicolons before media type
                   parameters are removed; the parameter values are returned in
                   a form where only the '``\``' and '``"``' characters are
                   escaped, and the values are quoted with double quotes only
                   if they need to be quoted.

                 | *qvalue* is the quality value of the media range.

                 | *media_type_params* is the media type parameters, as a list
                   of (parameter name, value) tuples.

                 | *extension_params* is the extension parameters, as a list
                   where each item is either a parameter string or a (parameter
                   name, value) tuple.
        :raises ValueError: if `value` is an invalid header
        """
        # Check if header is valid
        # Using Python stdlib's `re` module, there is currently no way to check
        # the match *and* get all the groups using the same regex, so we have
        # to do this in steps using multiple regexes.
        if cls.accept_compiled_re.match(value) is None:
            raise ValueError('Invalid value for an Accept header.')
        def generator(value):
            for match in (
                cls.media_range_n_accept_params_compiled_re.finditer(value)
            ):
                groups = match.groups()

                type_subtype = groups[0]

                media_type_params = cls._parse_media_type_params(
                    media_type_params_segment=groups[1],
                )

                media_range = cls._form_media_range(
                    type_subtype=type_subtype,
                    media_type_params=media_type_params,
                )

                # qvalue (groups[2]) and extension_params (groups[3]) are both
                # None if neither qvalue or extension parameters are found in
                # the match.

                qvalue = groups[2]
                qvalue = float(qvalue) if qvalue else 1.0

                extension_params = groups[3]
                if extension_params:
                    extension_params = cls.accept_ext_compiled_re.findall(
                        extension_params,
                    )
                    for index, (token_key, token_value) in enumerate(
                        extension_params
                    ):
                        if token_value:
                            if (
                                token_value.startswith('"') and
                                token_value.endswith('"')
                            ):
                                token_value = cls._process_quoted_string_token(
                                    token=token_value,
                                )
                                extension_params[index] = (
                                    token_key, token_value,
                                )
                        else:
                            extension_params[index] = token_key
                else:
                    extension_params = []

                yield (
                    media_range, qvalue, media_type_params, extension_params,
                )
        return generator(value=value)

    @classmethod
    def parse_offer(cls, offer):
        """
        Parse an offer into its component parts.

        :param offer: A media type or range in the format
                      ``type/subtype[;params]``.
        :return: A named tuple containing ``(*type*, *subtype*, *params*)``.

                 | *params* is a list containing ``(*parameter name*, *value*)``
                   values.

        :raises ValueError: If the offer does not match the required format.

        """
        if isinstance(offer, AcceptOffer):
            return offer
        match = cls.media_type_compiled_re.match(offer)
        if not match:
            raise ValueError('Invalid value for an Accept offer.')

        groups = match.groups()
        offer_type, offer_subtype = groups[0].split('/')
        offer_params = cls._parse_media_type_params(
            media_type_params_segment=groups[1],
        )
        if offer_type == '*' or offer_subtype == '*':
            raise ValueError('Invalid value for an Accept offer.')
        return AcceptOffer(
            offer_type.lower(),
            offer_subtype.lower(),
            tuple((name.lower(), value) for name, value in offer_params),
        )

    @classmethod
    def _parse_and_normalize_offers(cls, offers):
        """
        Throw out any offers that do not match the media range ABNF.

        :return: A list of offers split into the format ``[offer_index,
                 parsed_offer]``.

        """
        parsed_offers = []
        for index, offer in enumerate(offers):
            try:
                parsed_offer = cls.parse_offer(offer)
            except ValueError:
                continue
            parsed_offers.append([index, parsed_offer])
        return parsed_offers


class AcceptValidHeader(Accept):
    """
    Represent a valid ``Accept`` header.

    A valid header is one that conforms to :rfc:`RFC 7231, section 5.3.2
    <7231#section-5.3.2>`.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptValidHeader.__add__`).
    """

    @property
    def header_value(self):
        """(``str`` or ``None``) The header value."""
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        A list of (*media_range*, *qvalue*, *media_type_params*,
        *extension_params*) tuples, where

        *media_range* is the media range, including any media type parameters.
        The media range is returned in a canonicalised form (except the case of
        the characters are unchanged): unnecessary spaces around the semicolons
        before media type parameters are removed; the parameter values are
        returned in a form where only the '``\``' and '``"``' characters are
        escaped, and the values are quoted with double quotes only if they need
        to be quoted.

        *qvalue* is the quality value of the media range.

        *media_type_params* is the media type parameters, as a list of
        (parameter name, value) tuples.

        *extension_params* is the extension parameters, as a list where each
        item is either a parameter string or a (parameter name, value) tuple.
        """
        return self._parsed

    def __init__(self, header_value):
        """
        Create an :class:`AcceptValidHeader` instance.

        :param header_value: (``str``) header value.
        :raises ValueError: if `header_value` is an invalid value for an
                            ``Accept`` header.
        """
        self._header_value = header_value
        self._parsed = list(self.parse(header_value))
        self._parsed_nonzero = [item for item in self.parsed if item[1]]
        # item[1] is the qvalue

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, with media ranges ``str``\ s (including any media type
          parameters) as keys, and either qvalues ``float``\ s or (*qvalues*,
          *extension_params*) tuples as values, where *extension_params* is a
          ``str`` of the extension parameters segment of the header element,
          starting with the first '``;``'
        * a ``tuple`` or ``list``, where each item is either a header element
          ``str``, or a (*media_range*, *qvalue*, *extension_params*) ``tuple``
          or ``list`` where *media_range* is a ``str`` of the media range
          including any media type parameters, and *extension_params* is a
          ``str`` of the extension parameters segment of the header element,
          starting with the first '``;``'
        * an :class:`AcceptValidHeader`, :class:`AcceptNoHeader`, or
          :class:`AcceptInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or another
        :class:`AcceptValidHeader` instance, and the header value it represents
        is not `''`, then the two header values are joined with ``', '``, and a
        new :class:`AcceptValidHeader` instance with the new header value is
        returned.

        If `other` is a valid header value or another
        :class:`AcceptValidHeader` instance representing a header value of
        `''`; or if it is ``None`` or an :class:`AcceptNoHeader` instance; or
        if it is an invalid header value, or an :class:`AcceptInvalidHeader`
        instance, then a new :class:`AcceptValidHeader` instance with the same
        header value as ``self`` is returned.
        """
        if isinstance(other, AcceptValidHeader):
            if other.header_value == '':
                return self.__class__(header_value=self.header_value)
            else:
                return create_accept_header(
                    header_value=self.header_value + ', ' + other.header_value,
                )

        if isinstance(other, (AcceptNoHeader, AcceptInvalidHeader)):
            return self.__class__(header_value=self.header_value)

        return self._add_instance_and_non_accept_type(
            instance=self, other=other,
        )

    def __bool__(self):
        """
        Return whether ``self`` represents a valid ``Accept`` header.

        Return ``True`` if ``self`` represents a valid header, and ``False`` if
        it represents an invalid header, or the header not being in the
        request.

        For this class, it always returns ``True``.
        """
        return True
    __nonzero__ = __bool__  # Python 2

    def __contains__(self, offer):
        """
        Return ``bool`` indicating whether `offer` is acceptable.

        .. warning::

           The behavior of :meth:`AcceptValidHeader.__contains__` is currently
           being maintained for backward compatibility, but it will change in
           the future to better conform to the RFC.

        :param offer: (``str``) media type offer
        :return: (``bool``) Whether ``offer`` is acceptable according to the
                 header.

        This uses the old criterion of a match in
        :meth:`AcceptValidHeader._old_match`, which is not as specified in
        :rfc:`RFC 7231, section 5.3.2 <7231#section-5.3.2>`. It does not
        correctly take into account media type parameters:

            >>> 'text/html;p=1' in AcceptValidHeader('text/html')
            False

        or media ranges with ``q=0`` in the header::

            >>> 'text/html' in AcceptValidHeader('text/*, text/html;q=0')
            True
            >>> 'text/html' in AcceptValidHeader('text/html;q=0, */*')
            True

        (See the docstring for :meth:`AcceptValidHeader._old_match` for other
        problems with the old criterion for matching.)
        """
        warnings.warn(
            'The behavior of AcceptValidHeader.__contains__ is '
            'currently being maintained for backward compatibility, but it '
            'will change in the future to better conform to the RFC.',
            DeprecationWarning,
        )
        for (
            media_range, quality, media_type_params, extension_params
        ) in self._parsed_nonzero:
            if self._old_match(media_range, offer):
                return True
        return False

    def __iter__(self):
        """
        Return all the ranges with non-0 qvalues, in order of preference.

        .. warning::

           The behavior of this method is currently maintained for backward
           compatibility, but will change in the future.

        :return: iterator of all the media ranges in the header with non-0
                 qvalues, in descending order of qvalue. If two ranges have the
                 same qvalue, they are returned in the order of their positions
                 in the header, from left to right.

        Please note that this is a simple filter for the ranges in the header
        with non-0 qvalues, and is not necessarily the same as what the client
        prefers, e.g. ``'audio/basic;q=0, */*'`` means 'everything but
        audio/basic', but ``list(instance)`` would return only ``['*/*']``.
        """
        warnings.warn(
            'The behavior of AcceptLanguageValidHeader.__iter__ is currently '
            'maintained for backward compatibility, but will change in the '
            'future.',
            DeprecationWarning,
        )

        for media_range, qvalue, media_type_params, extension_params in sorted(
            self._parsed_nonzero,
            key=lambda i: i[1],
            reverse=True
        ):
            yield media_range

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptValidHeader.__add__`.
        """
        return self._add_instance_and_non_accept_type(
            instance=self, other=other, instance_on_the_right=True,
        )

    def __repr__(self):
        return '<{} ({!r})>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        r"""
        Return a tidied up version of the header value.

        e.g. If ``self.header_value`` is ``r',,text/html ; p1="\"\1\"" ;
        q=0.50; e1=1 ;e2  ,  text/plain ,'``, ``str(instance)`` returns
        ``r'text/html;p1="\"1\"";q=0.5;e1=1;e2, text/plain'``.
        """
        # self.parsed tuples are in the form: (media_range, qvalue,
        # media_type_params, extension_params)
        # self._iterable_to_header_element() requires iterable to be in the
        # form: (media_range, qvalue, extension_params_segment).
        return ', '.join(
            self._iterable_to_header_element(
                iterable=(
                    tuple_[0],  # media_range
                    tuple_[1],  # qvalue
                    self._form_extension_params_segment(
                        extension_params=tuple_[3],  # extension_params
                    )
                ),
            ) for tuple_ in self.parsed
        )

    def _add_instance_and_non_accept_type(
        self, instance, other, instance_on_the_right=False,
    ):
        if not other:
            return self.__class__(header_value=instance.header_value)

        other_header_value = self._python_value_to_header_str(value=other)

        if other_header_value == '':
            # if ``other`` is an object whose type we don't recognise, and
            # str(other) returns ''
            return self.__class__(header_value=instance.header_value)

        try:
            self.parse(value=other_header_value)
        except ValueError:  # invalid header value
            return self.__class__(header_value=instance.header_value)

        new_header_value = (
            (other_header_value + ', ' + instance.header_value)
            if instance_on_the_right
            else (instance.header_value + ', ' + other_header_value)
        )
        return self.__class__(header_value=new_header_value)

    def _old_match(self, mask, offer):
        """
        Check if the offer is covered by the mask

        ``offer`` may contain wildcards to facilitate checking if a ``mask``
        would match a 'permissive' offer.

        Wildcard matching forces the match to take place against the type or
        subtype of the mask and offer (depending on where the wildcard matches)

        .. warning::

           This is maintained for backward compatibility, and will be
           deprecated in the future.

        This method was WebOb's old criterion for deciding whether a media type
        matches a media range, used in

        - :meth:`AcceptValidHeader.__contains__`
        - :meth:`AcceptValidHeader.best_match`
        - :meth:`AcceptValidHeader.quality`

        It allows offers of *, */*, type/*, */subtype and types with no
        subtypes, which are not media types as specified in :rfc:`RFC 7231,
        section 5.3.2 <7231#section-5.3.2>`. This is also undocumented in any
        of the public APIs that uses this method.
        """
        # Match if comparisons are the same or either is a complete wildcard
        if (mask.lower() == offer.lower() or
                '*/*' in (mask, offer) or
                '*' == offer):
            return True

        # Set mask type with wildcard subtype for malformed masks
        try:
            mask_type, mask_subtype = [x.lower() for x in mask.split('/')]
        except ValueError:
            mask_type = mask
            mask_subtype = '*'

        # Set offer type with wildcard subtype for malformed offers
        try:
            offer_type, offer_subtype = [x.lower() for x in offer.split('/')]
        except ValueError:
            offer_type = offer
            offer_subtype = '*'

        if mask_subtype == '*':
            # match on type only
            if offer_type == '*':
                return True
            else:
                return mask_type.lower() == offer_type.lower()

        if mask_type == '*':
            # match on subtype only
            if offer_subtype == '*':
                return True
            else:
                return mask_subtype.lower() == offer_subtype.lower()

        if offer_subtype == '*':
            # match on type only
            return mask_type.lower() == offer_type.lower()

        if offer_type == '*':
            # match on subtype only
            return mask_subtype.lower() == offer_subtype.lower()

        return offer.lower() == mask.lower()

    def accept_html(self):
        """
        Return ``True`` if any HTML-like type is accepted.

        The HTML-like types are 'text/html', 'application/xhtml+xml',
        'application/xml' and 'text/xml'.
        """
        return bool(
            self.acceptable_offers(
                offers=[
                    'text/html',
                    'application/xhtml+xml',
                    'application/xml',
                    'text/xml',
                ],
            )
        )
    accepts_html = property(fget=accept_html, doc=accept_html.__doc__)
    # note the plural

    def acceptable_offers(self, offers):
        """
        Return the offers that are acceptable according to the header.

        The offers are returned in descending order of preference, where
        preference is indicated by the qvalue of the media range in the header
        that best matches the offer.

        This uses the matching rules described in :rfc:`RFC 7231, section 5.3.2
        <7231#section-5.3.2>`.

        Any offers that cannot be parsed via
        :meth:`.Accept.parse_offer` will be ignored.

        :param offers: ``iterable`` of ``str`` media types (media types can
                       include media type parameters) or pre-parsed instances
                       of :class:`.AcceptOffer`.
        :return: A list of tuples of the form (media type, qvalue), in
                 descending order of qvalue. Where two offers have the same
                 qvalue, they are returned in the same order as their order in
                 `offers`.
        """
        parsed = self.parsed

        # RFC 7231, section 3.1.1.1 "Media Type":
        # "The type, subtype, and parameter name tokens are case-insensitive.
        # Parameter values might or might not be case-sensitive, depending on
        # the semantics of the parameter name."
        lowercased_ranges = [
            (
                media_range.partition(';')[0].lower(),
                qvalue,
                tuple(
                    (name.lower(), value)
                    for name, value in media_type_params
                ),
            )
            for media_range, qvalue, media_type_params, __ in
            parsed
        ]
        lowercased_offers_parsed = self._parse_and_normalize_offers(offers)

        acceptable_offers_n_quality_factors = {}
        for offer_index, parsed_offer in lowercased_offers_parsed:
            offer = offers[offer_index]
            offer_type, offer_subtype, offer_media_type_params = parsed_offer
            for (
                range_type_subtype, range_qvalue, range_media_type_params,
            ) in lowercased_ranges:
                range_type, range_subtype = range_type_subtype.split('/', 1)

                # The specificity values below are based on the list in the
                # example in RFC 7231 section 5.3.2 explaining how "media
                # ranges can be overridden by more specific media ranges or
                # specific media types". We assign specificity to the list
                # items in reverse order, so specificity 4, 3, 2, 1 correspond
                # to 1, 2, 3, 4 in the list, respectively (so that higher
                # specificity has higher precedence).
                if (
                    offer_type == range_type
                    and offer_subtype == range_subtype
                ):
                    if range_media_type_params == ():
                        # If offer_media_type_params == () the offer and the
                        # range match exactly, with neither having media type
                        # parameters.
                        # If offer_media_type_params is not (), the offer and
                        # the range are a match. See the table towards the end
                        # of RFC 7231 section 5.3.2, where the media type
                        # 'text/html;level=3' matches the range 'text/html' in
                        # the header.
                        # Both cases are a match with a specificity of 3.
                        specificity = 3
                    elif offer_media_type_params == range_media_type_params:
                        specificity = 4
                    else:  # pragma: no cover
                        # no cover because of
                        # https://bitbucket.org/ned/coveragepy/issues/254/incorrect-coverage-on-continue-statement
                        continue
                else:
                    if range_subtype == '*' and offer_type == range_type:
                        specificity = 2
                    elif range_type_subtype == '*/*':
                        specificity = 1
                    else:  # pragma: no cover
                        # no cover because of
                        # https://bitbucket.org/ned/coveragepy/issues/254/incorrect-coverage-on-continue-statement
                        continue
                try:
                    if specificity <= (
                        acceptable_offers_n_quality_factors[offer][2]
                    ):
                        continue
                except KeyError:
                    # the entry for the offer is not already in
                    # acceptable_offers_n_quality_factors
                    pass
                acceptable_offers_n_quality_factors[offer] = (
                    range_qvalue,  # qvalue of matched range
                    offer_index,
                    specificity,  # specifity of matched range
                )

        acceptable_offers_n_quality_factors = [
            # key is offer, value[0] is qvalue, value[1] is offer_index
            (key, value[0], value[1])
            for key, value in acceptable_offers_n_quality_factors.items()
            if value[0]  # != 0.0
            # We have to filter out the offers with qvalues of 0 here instead
            # of just skipping them early in the large ``for`` loop because
            # that would not work for e.g. when the header is 'text/html;q=0,
            # text/html' (which does not make sense, but is nonetheless valid),
            # and offers is ['text/html']
        ]
        # sort by offer_index, ascending
        acceptable_offers_n_quality_factors.sort(key=lambda tuple_: tuple_[2])
        # (stable) sort by qvalue, descending
        acceptable_offers_n_quality_factors.sort(
            key=lambda tuple_: tuple_[1], reverse=True,
        )
        # drop offer_index
        acceptable_offers_n_quality_factors = [
            (item[0], item[1]) for item in acceptable_offers_n_quality_factors
        ]
        return acceptable_offers_n_quality_factors
        # If a media range is repeated in the header (which would not make
        # sense, but would be valid according to the rules in the RFC), an
        # offer for which the media range is the most specific match would take
        # its qvalue from the first appearance of the range in the header.

    def best_match(self, offers, default_match=None):
        """
        Return the best match from the sequence of media type `offers`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future.

           :meth:`AcceptValidHeader.best_match` uses its own algorithm (one not
           specified in :rfc:`RFC 7231 <7231>`) to determine what is a best
           match. The algorithm has many issues, and does not conform to
           :rfc:`RFC 7231 <7231>`.

        Each media type in `offers` is checked against each non-``q=0`` range
        in the header. If the two are a match according to WebOb's old
        criterion for a match, the quality value of the match is the qvalue of
        the media range from the header multiplied by the server quality value
        of the offer (if the server quality value is not supplied, it is 1).

        The offer in the match with the highest quality value is the best
        match. If there is more than one match with the highest qvalue, the
        match where the media range has a lower number of '*'s is the best
        match. If the two have the same number of '*'s, the one that shows up
        first in `offers` is the best match.

        :param offers: (iterable)

                       | Each item in the iterable may be a ``str`` media type,
                         or a (media type, server quality value) ``tuple`` or
                         ``list``. (The two may be mixed in the iterable.)

        :param default_match: (optional, any type) the value to be returned if
                              there is no match

        :return: (``str``, or the type of `default_match`)

                 | The offer that is the best match. If there is no match, the
                   value of `default_match` is returned.

        This uses the old criterion of a match in
        :meth:`AcceptValidHeader._old_match`, which is not as specified in
        :rfc:`RFC 7231, section 5.3.2 <7231#section-5.3.2>`. It does not
        correctly take into account media type parameters:

            >>> instance = AcceptValidHeader('text/html')
            >>> instance.best_match(offers=['text/html;p=1']) is None
            True

        or media ranges with ``q=0`` in the header::

            >>> instance = AcceptValidHeader('text/*, text/html;q=0')
            >>> instance.best_match(offers=['text/html'])
            'text/html'

            >>> instance = AcceptValidHeader('text/html;q=0, */*')
            >>> instance.best_match(offers=['text/html'])
            'text/html'

        (See the docstring for :meth:`AcceptValidHeader._old_match` for other
        problems with the old criterion for matching.)

        Another issue is that this method considers the best matching range for
        an offer to be the matching range with the highest quality value,
        (where quality values are tied, the most specific media range is
        chosen); whereas :rfc:`RFC 7231, section 5.3.2 <7231#section-5.3.2>`
        specifies that we should consider the best matching range for a media
        type offer to be the most specific matching range.::

            >>> instance = AcceptValidHeader('text/html;q=0.5, text/*')
            >>> instance.best_match(offers=['text/html', 'text/plain'])
            'text/html'
        """
        warnings.warn(
            'The behavior of AcceptValidHeader.best_match is currently being '
            'maintained for backward compatibility, but it will be deprecated'
            ' in the future, as it does not conform to the RFC.',
            DeprecationWarning,
        )
        best_quality = -1
        best_offer = default_match
        matched_by = '*/*'
        for offer in offers:
            if isinstance(offer, (tuple, list)):
                offer, server_quality = offer
            else:
                server_quality = 1
            for item in self._parsed_nonzero:
                mask = item[0]
                quality = item[1]
                possible_quality = server_quality * quality
                if possible_quality < best_quality:
                    continue
                elif possible_quality == best_quality:
                    # 'text/plain' overrides 'message/*' overrides '*/*'
                    # (if all match w/ the same q=)
                    if matched_by.count('*') <= mask.count('*'):
                        continue
                if self._old_match(mask, offer):
                    best_quality = possible_quality
                    best_offer = offer
                    matched_by = mask
        return best_offer

    def quality(self, offer):
        """
        Return quality value of given offer, or ``None`` if there is no match.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future.

        :param offer: (``str``) media type offer
        :return: (``float`` or ``None``)

                 | The highest quality value from the media range(s) that match
                   the `offer`, or ``None`` if there is no match.

        This uses the old criterion of a match in
        :meth:`AcceptValidHeader._old_match`, which is not as specified in
        :rfc:`RFC 7231, section 5.3.2 <7231#section-5.3.2>`. It does not
        correctly take into account media type parameters:

            >>> instance = AcceptValidHeader('text/html')
            >>> instance.quality('text/html;p=1') is None
            True

        or media ranges with ``q=0`` in the header::

            >>> instance = AcceptValidHeader('text/*, text/html;q=0')
            >>> instance.quality('text/html')
            1.0
            >>> AcceptValidHeader('text/html;q=0, */*').quality('text/html')
            1.0

        (See the docstring for :meth:`AcceptValidHeader._old_match` for other
        problems with the old criterion for matching.)

        Another issue is that this method considers the best matching range for
        an offer to be the matching range with the highest quality value,
        whereas :rfc:`RFC 7231, section 5.3.2 <7231#section-5.3.2>` specifies
        that we should consider the best matching range for a media type offer
        to be the most specific matching range.::

            >>> instance = AcceptValidHeader('text/html;q=0.5, text/*')
            >>> instance.quality('text/html')
            1.0
        """
        warnings.warn(
            'The behavior of AcceptValidHeader.quality is currently being '
            'maintained for backward compatibility, but it will be deprecated '
            'in the future, as it does not conform to the RFC.',
            DeprecationWarning,
        )
        bestq = 0
        for item in self.parsed:
            media_range = item[0]
            qvalue = item[1]
            if self._old_match(media_range, offer):
                bestq = max(bestq, qvalue)
        return bestq or None


class MIMEAccept(Accept):
    """
    Backwards compatibility shim for the new functionality provided by
    AcceptValidHeader, AcceptInvalidHeader, or AcceptNoHeader, that acts like
    the old MIMEAccept from WebOb version 1.7 or lower.

    This shim does use the newer Accept header parsing, which will mean your
    application may be less liberal in what Accept headers are correctly
    parsed. It is recommended that user agents be updated to send appropriate
    Accept headers that are valid according to rfc:`RFC 7231, section 5.3.2
    <7231#section-5.3.2>`

    .. deprecated:: 1.8

       Instead of directly creating the Accept object, please see:
       :func:`create_accept_header(header_value)
       <webob.acceptparse.create_accept_header>`, which will create the
       appropriate object.

       This shim has an extended deprecation period to allow for application
       developers to switch the to new API.

    """

    def __init__(self, header_value):
        warnings.warn(
            'The MIMEAccept class has been replaced by '
            'webob.acceptparse.create_accept_header. This compatibility shim '
            'will be deprecated in a future version of WebOb.',
            DeprecationWarning
        )
        self._accept = create_accept_header(header_value)
        if self._accept.parsed:
            self._parsed = [(media, q) for (media, q, _, _) in self._accept.parsed]
            self._parsed_nonzero = [(m, q) for (m, q) in self._parsed if q]
        else:
            self._parsed = []
            self._parsed_nonzero = []

    @staticmethod
    def parse(value):
        try:
            parsed_accepted = Accept.parse(value)

            for (media, q, _, _) in parsed_accepted:
                yield (media, q)
        except ValueError:
            pass

    def __repr__(self):
        return self._accept.__repr__()

    def __iter__(self):
        return self._accept.__iter__()

    def __str__(self):
        return self._accept.__str__()

    def __add__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(str(self._accept.__add__(other._accept)))
        else:
            return self.__class__(str(self._accept.__add__(other)))

    def __radd__(self, other):
        return self.__class__(str(self._accept.__radd__(other)))

    def __contains__(self, offer):
        return offer in self._accept

    def quality(self, offer):
        return self._accept.quality(offer)

    def best_match(self, offers, default_match=None):
        return self._accept.best_match(offers, default_match=default_match)

    def accept_html(self):
        return self._accept.accept_html()


class _AcceptInvalidOrNoHeader(Accept):
    """
    Represent when an ``Accept`` header is invalid or not in request.

    This is the base class for the behaviour that :class:`.AcceptInvalidHeader`
    and :class:`.AcceptNoHeader` have in common.

    :rfc:`7231` does not provide any guidance on what should happen if the
    ``Accept`` header has an invalid value. This implementation disregards the
    header when the header is invalid, so :class:`.AcceptInvalidHeader` and
    :class:`.AcceptNoHeader` have much behaviour in common.
    """

    def __bool__(self):
        """
        Return whether ``self`` represents a valid ``Accept`` header.

        Return ``True`` if ``self`` represents a valid header, and ``False`` if
        it represents an invalid header, or the header not being in the
        request.

        For this class, it always returns ``False``.
        """
        return False
    __nonzero__ = __bool__  # Python 2

    def __contains__(self, offer):
        """
        Return ``bool`` indicating whether `offer` is acceptable.

        .. warning::

           The behavior of ``.__contains__`` for the ``Accept`` classes is
           currently being maintained for backward compatibility, but it will
           change in the future to better conform to the RFC.

        :param offer: (``str``) media type offer
        :return: (``bool``) Whether ``offer`` is acceptable according to the
                 header.

        For this class, either there is no ``Accept`` header in the request, or
        the header is invalid, so any media type is acceptable, and this always
        returns ``True``.
        """
        warnings.warn(
            'The behavior of .__contains__ for the Accept classes is '
            'currently being maintained for backward compatibility, but it '
            'will change in the future to better conform to the RFC.',
            DeprecationWarning,
        )
        return True

    def __iter__(self):
        """
        Return all the ranges with non-0 qvalues, in order of preference.

        .. warning::

           The behavior of this method is currently maintained for backward
           compatibility, but will change in the future.

        :return: iterator of all the media ranges in the header with non-0
                 qvalues, in descending order of qvalue. If two ranges have the
                 same qvalue, they are returned in the order of their positions
                 in the header, from left to right.

        When there is no ``Accept`` header in the request or the header is
        invalid, there are no media ranges, so this always returns an empty
        iterator.
        """
        warnings.warn(
            'The behavior of AcceptValidHeader.__iter__ is currently '
            'maintained for backward compatibility, but will change in the '
            'future.',
            DeprecationWarning,
        )
        return iter(())

    def accept_html(self):
        """
        Return ``True`` if any HTML-like type is accepted.

        The HTML-like types are 'text/html', 'application/xhtml+xml',
        'application/xml' and 'text/xml'.

        When the header is invalid, or there is no `Accept` header in the
        request, all `offers` are considered acceptable, so this always returns
        ``True``.
        """
        return bool(
            self.acceptable_offers(
                offers=[
                    'text/html',
                    'application/xhtml+xml',
                    'application/xml',
                    'text/xml',
                ],
            )
        )
    accepts_html = property(fget=accept_html, doc=accept_html.__doc__)
    # note the plural

    def acceptable_offers(self, offers):
        """
        Return the offers that are acceptable according to the header.

        Any offers that cannot be parsed via
        :meth:`.Accept.parse_offer` will be ignored.

        :param offers: ``iterable`` of ``str`` media types (media types can
                       include media type parameters)
        :return: When the header is invalid, or there is no ``Accept`` header
                 in the request, all `offers` are considered acceptable, so
                 this method returns a list of (media type, qvalue) tuples
                 where each offer in `offers` is paired with the qvalue of 1.0,
                 in the same order as in `offers`.
        """
        return [
            (offers[offer_index], 1.0)
            for offer_index, _
            # avoid returning any offers that don't match the grammar so
            # that the return values here are consistent with what would be
            # returned in AcceptValidHeader
            in self._parse_and_normalize_offers(offers)
        ]

    def best_match(self, offers, default_match=None):
        """
        Return the best match from the sequence of language tag `offers`.

        This is the ``.best_match()`` method for when the header is invalid or
        not found in the request, corresponding to
        :meth:`AcceptValidHeader.best_match`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future (see the documentation for
           :meth:`AcceptValidHeader.best_match`).

        When the header is invalid, or there is no `Accept` header in the
        request, all `offers` are considered acceptable, so the best match is
        the media type in `offers` with the highest server quality value (if
        the server quality value is not supplied for a media type, it is 1).

        If more than one media type in `offers` have the same highest server
        quality value, then the one that shows up first in `offers` is the best
        match.

        :param offers: (iterable)

                       | Each item in the iterable may be a ``str`` media type,
                         or a (media type, server quality value) ``tuple`` or
                         ``list``. (The two may be mixed in the iterable.)

        :param default_match: (optional, any type) the value to be returned if
                              `offers` is empty.

        :return: (``str``, or the type of `default_match`)

                 | The offer that has the highest server quality value.  If
                   `offers` is empty, the value of `default_match` is returned.
        """
        warnings.warn(
            'The behavior of .best_match for the Accept classes is currently '
            'being maintained for backward compatibility, but the method will'
            ' be deprecated in the future, as its behavior is not specified '
            'in (and currently does not conform to) RFC 7231.',
            DeprecationWarning,
        )
        best_quality = -1
        best_offer = default_match
        for offer in offers:
            if isinstance(offer, (list, tuple)):
                offer, quality = offer
            else:
                quality = 1
            if quality > best_quality:
                best_offer = offer
                best_quality = quality
        return best_offer

    def quality(self, offer):
        """
        Return quality value of given offer, or ``None`` if there is no match.

        This is the ``.quality()`` method for when the header is invalid or not
        found in the request, corresponding to
        :meth:`AcceptValidHeader.quality`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future (see the documentation for
           :meth:`AcceptValidHeader.quality`).

        :param offer: (``str``) media type offer
        :return: (``float``) ``1.0``.

        When the ``Accept`` header is invalid or not in the request, all offers
        are equally acceptable, so 1.0 is always returned.
        """
        warnings.warn(
            'The behavior of .quality for the Accept classes is currently '
            'being maintained for backward compatibility, but the method will'
            ' be deprecated in the future, as its behavior does not conform to'
            'RFC 7231.',
            DeprecationWarning,
        )
        return 1.0


class AcceptNoHeader(_AcceptInvalidOrNoHeader):
    """
    Represent when there is no ``Accept`` header in the request.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptNoHeader.__add__`).
    """

    @property
    def header_value(self):
        """
        (``str`` or ``None``) The header value.

        As there is no header in the request, this is ``None``.
        """
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        As there is no header in the request, this is ``None``.
        """
        return self._parsed

    def __init__(self):
        """
        Create an :class:`AcceptNoHeader` instance.
        """
        self._header_value = None
        self._parsed = None
        self._parsed_nonzero = None

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, with media ranges ``str``\ s (including any media type
          parameters) as keys, and either qvalues ``float``\ s or (*qvalues*,
          *extension_params*) tuples as values, where *extension_params* is a
          ``str`` of the extension parameters segment of the header element,
          starting with the first '``;``'
        * a ``tuple`` or ``list``, where each item is either a header element
          ``str``, or a (*media_range*, *qvalue*, *extension_params*) ``tuple``
          or ``list`` where *media_range* is a ``str`` of the media range
          including any media type parameters, and *extension_params* is a
          ``str`` of the extension parameters segment of the header element,
          starting with the first '``;``'
        * an :class:`AcceptValidHeader`, :class:`AcceptNoHeader`, or
          :class:`AcceptInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or an :class:`AcceptValidHeader`
        instance, a new :class:`AcceptValidHeader` instance with the valid
        header value is returned.

        If `other` is ``None``, an :class:`AcceptNoHeader` instance, an invalid
        header value, or an :class:`AcceptInvalidHeader` instance, a new
        :class:`AcceptNoHeader` instance is returned.
        """
        if isinstance(other, AcceptValidHeader):
            return AcceptValidHeader(header_value=other.header_value)

        if isinstance(other, (AcceptNoHeader, AcceptInvalidHeader)):
            return self.__class__()

        return self._add_instance_and_non_accept_type(
            instance=self, other=other,
        )

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptNoHeader.__add__`.
        """
        return self.__add__(other=other)

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    def __str__(self):
        """Return the ``str`` ``'<no header in request>'``."""
        return '<no header in request>'

    def _add_instance_and_non_accept_type(self, instance, other):
        if other is None:
            return self.__class__()

        other_header_value = self._python_value_to_header_str(value=other)

        try:
            return AcceptValidHeader(header_value=other_header_value)
        except ValueError:  # invalid header value
            return self.__class__()


class AcceptInvalidHeader(_AcceptInvalidOrNoHeader):
    """
    Represent an invalid ``Accept`` header.

    An invalid header is one that does not conform to
    :rfc:`7231#section-5.3.2`.

    :rfc:`7231` does not provide any guidance on what should happen if the
    ``Accept`` header has an invalid value. This implementation disregards the
    header, and treats it as if there is no ``Accept`` header in the request.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptInvalidHeader.__add__`).
    """

    @property
    def header_value(self):
        """(``str`` or ``None``) The header value."""
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        As the header is invalid and cannot be parsed, this is ``None``.
        """
        return self._parsed

    def __init__(self, header_value):
        """
        Create an :class:`AcceptInvalidHeader` instance.
        """
        self._header_value = header_value
        self._parsed = None
        self._parsed_nonzero = None

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, with media ranges ``str``\ s (including any media type
          parameters) as keys, and either qvalues ``float``\ s or (*qvalues*,
          *extension_params*) tuples as values, where *extension_params* is a
          ``str`` of the extension parameters segment of the header element,
          starting with the first '``;``'
        * a ``tuple`` or ``list``, where each item is either a header element
          ``str``, or a (*media_range*, *qvalue*, *extension_params*) ``tuple``
          or ``list`` where *media_range* is a ``str`` of the media range
          including any media type parameters, and *extension_params* is a
          ``str`` of the extension parameters segment of the header element,
          starting with the first '``;``'
        * an :class:`AcceptValidHeader`, :class:`AcceptNoHeader`, or
          :class:`AcceptInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or an :class:`AcceptValidHeader`
        instance, then a new :class:`AcceptValidHeader` instance with the valid
        header value is returned.

        If `other` is ``None``, an :class:`AcceptNoHeader` instance, an invalid
        header value, or an :class:`AcceptInvalidHeader` instance, a new
        :class:`AcceptNoHeader` instance is returned.
        """
        if isinstance(other, AcceptValidHeader):
            return AcceptValidHeader(header_value=other.header_value)

        if isinstance(other, (AcceptNoHeader, AcceptInvalidHeader)):
            return AcceptNoHeader()

        return self._add_instance_and_non_accept_type(
            instance=self, other=other,
        )

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptValidHeader.__add__`.
        """
        return self._add_instance_and_non_accept_type(
            instance=self, other=other, instance_on_the_right=True,
        )

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)
        # We do not display the header_value, as it is untrusted input. The
        # header_value could always be easily obtained from the .header_value
        # property.

    def __str__(self):
        """Return the ``str`` ``'<invalid header value>'``."""
        return '<invalid header value>'

    def _add_instance_and_non_accept_type(
        self, instance, other, instance_on_the_right=False,
    ):
        if other is None:
            return AcceptNoHeader()

        other_header_value = self._python_value_to_header_str(value=other)

        try:
            return AcceptValidHeader(header_value=other_header_value)
        except ValueError:  # invalid header value
            return AcceptNoHeader()


def create_accept_header(header_value):
    """
    Create an object representing the ``Accept`` header in a request.

    :param header_value: (``str``) header value
    :return: If `header_value` is ``None``, an :class:`AcceptNoHeader`
             instance.

             | If `header_value` is a valid ``Accept`` header, an
               :class:`AcceptValidHeader` instance.

             | If `header_value` is an invalid ``Accept`` header, an
               :class:`AcceptInvalidHeader` instance.
    """
    if header_value is None:
        return AcceptNoHeader()
    try:
        return AcceptValidHeader(header_value=header_value)
    except ValueError:
        return AcceptInvalidHeader(header_value=header_value)


def accept_property():
    doc = """
        Property representing the ``Accept`` header.

        (:rfc:`RFC 7231, section 5.3.2 <7231#section-5.3.2>`)

        The header value in the request environ is parsed and a new object
        representing the header is created every time we *get* the value of the
        property. (*set* and *del* change the header value in the request
        environ, and do not involve parsing.)
    """

    ENVIRON_KEY = 'HTTP_ACCEPT'

    def fget(request):
        """Get an object representing the header in the request."""
        return create_accept_header(
            header_value=request.environ.get(ENVIRON_KEY)
        )

    def fset(request, value):
        """
        Set the corresponding key in the request environ.

        `value` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, with media ranges ``str``\ s (including any media type
          parameters) as keys, and either qvalues ``float``\ s or (*qvalues*,
          *extension_params*) tuples as values, where *extension_params* is a
          ``str`` of the extension parameters segment of the header element,
          starting with the first '``;``'
        * a ``tuple`` or ``list``, where each item is either a header element
          ``str``, or a (*media_range*, *qvalue*, *extension_params*) ``tuple``
          or ``list`` where *media_range* is a ``str`` of the media range
          including any media type parameters, and *extension_params* is a
          ``str`` of the extension parameters segment of the header element,
          starting with the first '``;``'
        * an :class:`AcceptValidHeader`, :class:`AcceptNoHeader`, or
          :class:`AcceptInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``
        """
        if value is None or isinstance(value, AcceptNoHeader):
            fdel(request=request)
        else:
            if isinstance(value, (AcceptValidHeader, AcceptInvalidHeader)):
                header_value = value.header_value
            else:
                header_value = Accept._python_value_to_header_str(value=value)
            request.environ[ENVIRON_KEY] = header_value

    def fdel(request):
        """Delete the corresponding key from the request environ."""
        try:
            del request.environ[ENVIRON_KEY]
        except KeyError:
            pass

    return property(fget, fset, fdel, textwrap.dedent(doc))


class AcceptCharset(object):
    """
    Represent an ``Accept-Charset`` header.

    Base class for :class:`AcceptCharsetValidHeader`,
    :class:`AcceptCharsetNoHeader`, and :class:`AcceptCharsetInvalidHeader`.
    """

    # RFC 7231 Section 3.1.1.2 "Charset":
    # charset = token
    charset_re = token_re
    # RFC 7231 Section 5.3.3 "Accept-Charset":
    # Accept-Charset = 1#( ( charset / "*" ) [ weight ] )
    charset_n_weight_re = _item_n_weight_re(item_re=charset_re)
    charset_n_weight_compiled_re = re.compile(charset_n_weight_re)
    accept_charset_compiled_re = _list_1_or_more__compiled_re(
        element_re=charset_n_weight_re,
    )

    @classmethod
    def _python_value_to_header_str(cls, value):
        if isinstance(value, str):
            header_str = value
        else:
            if hasattr(value, 'items'):
                value = sorted(
                    value.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            if isinstance(value, (tuple, list)):
                result = []
                for item in value:
                    if isinstance(item, (tuple, list)):
                        item = _item_qvalue_pair_to_header_element(pair=item)
                    result.append(item)
                header_str = ', '.join(result)
            else:
                header_str = str(value)
        return header_str

    @classmethod
    def parse(cls, value):
        """
        Parse an ``Accept-Charset`` header.

        :param value: (``str``) header value
        :return: If `value` is a valid ``Accept-Charset`` header, returns an
                 iterator of (charset, quality value) tuples, as parsed from
                 the header from left to right.
        :raises ValueError: if `value` is an invalid header
        """
        # Check if header is valid
        # Using Python stdlib's `re` module, there is currently no way to check
        # the match *and* get all the groups using the same regex, so we have
        # to use one regex to check the match, and another to get the groups.
        if cls.accept_charset_compiled_re.match(value) is None:
            raise ValueError('Invalid value for an Accept-Charset header.')
        def generator(value):
            for match in (cls.charset_n_weight_compiled_re.finditer(value)):
                charset = match.group(1)
                qvalue = match.group(2)
                qvalue = float(qvalue) if qvalue else 1.0
                yield (charset, qvalue)
        return generator(value=value)


class AcceptCharsetValidHeader(AcceptCharset):
    """
    Represent a valid ``Accept-Charset`` header.

    A valid header is one that conforms to :rfc:`RFC 7231, section 5.3.3
    <7231#section-5.3.3>`.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptCharsetValidHeader.__add__`).
    """

    @property
    def header_value(self):
        """(``str``) The header value."""
        return self._header_value

    @property
    def parsed(self):
        """
        (``list``) Parsed form of the header.

        A list of (charset, quality value) tuples.
        """
        return self._parsed

    def __init__(self, header_value):
        """
        Create an :class:`AcceptCharsetValidHeader` instance.

        :param header_value: (``str``) header value.
        :raises ValueError: if `header_value` is an invalid value for an
                            ``Accept-Charset`` header.
        """
        self._header_value = header_value
        self._parsed = list(self.parse(header_value))
        self._parsed_nonzero = [
            item for item in self.parsed if item[1]  # item[1] is the qvalue
        ]

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, where keys are charsets and values are qvalues
        * a ``tuple`` or ``list``, where each item is a charset ``str`` or a
          ``tuple`` or ``list`` (charset, qvalue) pair (``str``\ s and pairs
          can be mixed within the ``tuple`` or ``list``)
        * an :class:`AcceptCharsetValidHeader`, :class:`AcceptCharsetNoHeader`,
          or :class:`AcceptCharsetInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or another
        :class:`AcceptCharsetValidHeader` instance, the two header values are
        joined with ``', '``, and a new :class:`AcceptCharsetValidHeader`
        instance with the new header value is returned.

        If `other` is ``None``, an :class:`AcceptCharsetNoHeader` instance, an
        invalid header value, or an :class:`AcceptCharsetInvalidHeader`
        instance, a new :class:`AcceptCharsetValidHeader` instance with the
        same header value as ``self`` is returned.
        """
        if isinstance(other, AcceptCharsetValidHeader):
            return create_accept_charset_header(
                header_value=self.header_value + ', ' + other.header_value,
            )

        if isinstance(
            other, (AcceptCharsetNoHeader, AcceptCharsetInvalidHeader)
        ):
            return self.__class__(header_value=self.header_value)

        return self._add_instance_and_non_accept_charset_type(
            instance=self, other=other,
        )

    def __bool__(self):
        """
        Return whether ``self`` represents a valid ``Accept-Charset`` header.

        Return ``True`` if ``self`` represents a valid header, and ``False`` if
        it represents an invalid header, or the header not being in the
        request.

        For this class, it always returns ``True``.
        """
        return True
    __nonzero__ = __bool__  # Python 2

    def __contains__(self, offer):
        """
        Return ``bool`` indicating whether `offer` is acceptable.

        .. warning::

           The behavior of :meth:`AcceptCharsetValidHeader.__contains__` is
           currently being maintained for backward compatibility, but it will
           change in the future to better conform to the RFC.

        :param offer: (``str``) charset offer
        :return: (``bool``) Whether ``offer`` is acceptable according to the
                 header.

        This does not fully conform to :rfc:`RFC 7231, section 5.3.3
        <7231#section-5.3.3>`: it incorrect interprets ``*`` to mean 'match any
        charset in the header', rather than 'match any charset that is not
        mentioned elsewhere in the header'::

            >>> 'UTF-8' in AcceptCharsetValidHeader('UTF-8;q=0, *')
            True
        """
        warnings.warn(
            'The behavior of AcceptCharsetValidHeader.__contains__ is '
            'currently being maintained for backward compatibility, but it '
            'will change in the future to better conform to the RFC.',
            DeprecationWarning,
        )
        for mask, quality in self._parsed_nonzero:
            if self._old_match(mask, offer):
                return True
        return False

    def __iter__(self):
        """
        Return all the items with non-0 qvalues, in order of preference.

        .. warning::

           The behavior of this method is currently maintained for backward
           compatibility, but will change in the future.

        :return: iterator of all the items (charset or ``*``) in the header
                 with non-0 qvalues, in descending order of qvalue. If two
                 items have the same qvalue, they are returned in the order of
                 their positions in the header, from left to right.

        Please note that this is a simple filter for the items in the header
        with non-0 qvalues, and is not necessarily the same as what the client
        prefers, e.g. ``'utf-7;q=0, *'`` means 'everything but utf-7', but
        ``list(instance)`` would return only ``['*']``.
        """
        warnings.warn(
            'The behavior of AcceptCharsetValidHeader.__iter__ is currently '
            'maintained for backward compatibility, but will change in the '
            'future.',
            DeprecationWarning,
        )
        for m,q in sorted(
            self._parsed_nonzero,
            key=lambda i: i[1],
            reverse=True
        ):
            yield m

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptCharsetValidHeader.__add__`.
        """
        return self._add_instance_and_non_accept_charset_type(
            instance=self, other=other, instance_on_the_right=True,
        )

    def __repr__(self):
        return '<{} ({!r})>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        r"""
        Return a tidied up version of the header value.

        e.g. If the ``header_value`` is ``', \t,iso-8859-5;q=0.000 \t,
        utf-8;q=1.000, UTF-7, unicode-1-1;q=0.210  ,'``, ``str(instance)``
        returns ``'iso-8859-5;q=0, utf-8, UTF-7, unicode-1-1;q=0.21'``.
        """
        return ', '.join(
            _item_qvalue_pair_to_header_element(pair=tuple_)
            for tuple_ in self.parsed
        )

    def _add_instance_and_non_accept_charset_type(
        self, instance, other, instance_on_the_right=False,
    ):
        if not other:
            return self.__class__(header_value=instance.header_value)

        other_header_value = self._python_value_to_header_str(value=other)

        try:
            self.parse(value=other_header_value)
        except ValueError:  # invalid header value
            return self.__class__(header_value=instance.header_value)

        new_header_value = (
            (other_header_value + ', ' + instance.header_value)
            if instance_on_the_right
            else (instance.header_value + ', ' + other_header_value)
        )
        return self.__class__(header_value=new_header_value)

    def _old_match(self, mask, offer):
        """
        Return whether charset offer matches header item (charset or ``*``).

        .. warning::

           This is maintained for backward compatibility, and will be
           deprecated in the future.

        This method was WebOb's old criterion for deciding whether a charset
        matches a header item (charset or ``*``), used in

        - :meth:`AcceptCharsetValidHeader.__contains__`
        - :meth:`AcceptCharsetValidHeader.best_match`
        - :meth:`AcceptCharsetValidHeader.quality`

        It does not conform to :rfc:`RFC 7231, section 5.3.3
        <7231#section-5.3.3>` in that it does not interpret ``*`` values in the
        header correctly: ``*`` should only match charsets not mentioned
        elsewhere in the header.
        """
        return mask == '*' or offer.lower() == mask.lower()

    def acceptable_offers(self, offers):
        """
        Return the offers that are acceptable according to the header.

        The offers are returned in descending order of preference, where
        preference is indicated by the qvalue of the charset or ``*`` in the
        header matching the offer.

        This uses the matching rules described in :rfc:`RFC 7231, section 5.3.3
        <7231#section-5.3.3>`.

        :param offers: ``iterable`` of ``str`` charsets
        :return: A list of tuples of the form (charset, qvalue), in descending
                 order of qvalue. Where two offers have the same qvalue, they
                 are returned in the same order as their order in `offers`.
        """
        lowercased_parsed = [
            (charset.lower(), qvalue) for (charset, qvalue) in self.parsed
        ]
        lowercased_offers = [offer.lower() for offer in offers]

        not_acceptable_charsets = set()
        acceptable_charsets = dict()
        asterisk_qvalue = None

        for charset, qvalue in lowercased_parsed:
            if charset == '*':
                if asterisk_qvalue is None:
                    asterisk_qvalue = qvalue
            elif (
                charset not in acceptable_charsets and charset not in
                not_acceptable_charsets
                # if we have not already encountered this charset in the header
            ):
                if qvalue == 0.0:
                    not_acceptable_charsets.add(charset)
                else:
                    acceptable_charsets[charset] = qvalue
        acceptable_charsets = list(acceptable_charsets.items())
        # Sort acceptable_charsets by qvalue, descending order
        acceptable_charsets.sort(key=lambda tuple_: tuple_[1], reverse=True)

        filtered_offers = []
        for index, offer in enumerate(lowercased_offers):
            # If offer matches a non-* charset with q=0, it is filtered out
            if any((
                (offer == charset) for charset in not_acceptable_charsets
            )):
                continue

            matched_charset_qvalue = None
            for charset, qvalue in acceptable_charsets:
                if offer == charset:
                    matched_charset_qvalue = qvalue
                    break
            else:
                if asterisk_qvalue:
                    matched_charset_qvalue = asterisk_qvalue
            if matched_charset_qvalue is not None:  # if there was a match
                filtered_offers.append((
                    offers[index], matched_charset_qvalue, index
                ))

        # sort by position in `offers` argument, ascending
        filtered_offers.sort(key=lambda tuple_: tuple_[2])
        # When qvalues are tied, position in `offers` is the tiebreaker.

        # sort by qvalue, descending
        filtered_offers.sort(key=lambda tuple_: tuple_[1], reverse=True)

        return [(item[0], item[1]) for item in filtered_offers]
        # (offer, qvalue), dropping the position

    def best_match(self, offers, default_match=None):
        """
        Return the best match from the sequence of charset `offers`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future.

           :meth:`AcceptCharsetValidHeader.best_match`  has many issues, and
           does not conform to :rfc:`RFC 7231 <7231>`.

        Each charset in `offers` is checked against each non-``q=0`` item
        (charset or ``*``) in the header. If the two are a match according to
        WebOb's old criterion for a match, the quality value of the match is
        the qvalue of the item from the header multiplied by the server quality
        value of the offer (if the server quality value is not supplied, it is
        1).

        The offer in the match with the highest quality value is the best
        match. If there is more than one match with the highest qvalue, the one
        that shows up first in `offers` is the best match.

        :param offers: (iterable)

                       | Each item in the iterable may be a ``str`` charset, or
                         a (charset, server quality value) ``tuple`` or
                         ``list``.  (The two may be mixed in the iterable.)

        :param default_match: (optional, any type) the value to be returned if
                              there is no match

        :return: (``str``, or the type of `default_match`)

                 | The offer that is the best match. If there is no match, the
                   value of `default_match` is returned.

        The algorithm behind this method was written for the ``Accept`` header
        rather than the ``Accept-Charset`` header. It uses the old criterion of
        a match in :meth:`AcceptCharsetValidHeader._old_match`, which does not
        conform to :rfc:`RFC 7231, section 5.3.3 <7231#section-5.3.3>`, in that
        it does not interpret ``*`` values in the header correctly: ``*``
        should only match charsets not mentioned elsewhere in the header::

            >>> AcceptCharsetValidHeader('utf-8;q=0, *').best_match(['utf-8'])
            'utf-8'
        """
        warnings.warn(
            'The behavior of AcceptCharsetValidHeader.best_match is currently'
            ' being maintained for backward compatibility, but it will be '
            'deprecated in the future, as it does not conform to the RFC.',
            DeprecationWarning,
        )
        best_quality = -1
        best_offer = default_match
        matched_by = '*/*'
        for offer in offers:
            if isinstance(offer, (tuple, list)):
                offer, server_quality = offer
            else:
                server_quality = 1
            for mask, quality in self._parsed_nonzero:
                possible_quality = server_quality * quality
                if possible_quality < best_quality:
                    continue
                elif possible_quality == best_quality:
                    # 'text/plain' overrides 'message/*' overrides '*/*'
                    # (if all match w/ the same q=)
                    # [We can see that this was written for the Accept header,
                    # not the Accept-Charset header.]
                    if matched_by.count('*') <= mask.count('*'):
                        continue
                if self._old_match(mask, offer):
                    best_quality = possible_quality
                    best_offer = offer
                    matched_by = mask
        return best_offer

    def quality(self, offer):
        """
        Return quality value of given offer, or ``None`` if there is no match.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future.

        :param offer: (``str``) charset offer
        :return: (``float`` or ``None``)

                 | The quality value from the charset that matches the `offer`,
                   or ``None`` if there is no match.

        This uses the old criterion of a match in
        :meth:`AcceptCharsetValidHeader._old_match`, which does not conform to
        :rfc:`RFC 7231, section 5.3.3 <7231#section-5.3.3>`, in that it does
        not interpret ``*`` values in the header correctly: ``*`` should only
        match charsets not mentioned elsewhere in the header::

            >>> AcceptCharsetValidHeader('utf-8;q=0, *').quality('utf-8')
            1.0
            >>> AcceptCharsetValidHeader('utf-8;q=0.9, *').quality('utf-8')
            1.0
        """
        warnings.warn(
            'The behavior of AcceptCharsetValidHeader.quality is currently '
            'being maintained for backward compatibility, but it will be '
            'deprecated in the future, as it does not conform to the RFC.',
            DeprecationWarning,
        )
        bestq = 0
        for mask, q in self.parsed:
            if self._old_match(mask, offer):
                bestq = max(bestq, q)
        return bestq or None


class _AcceptCharsetInvalidOrNoHeader(AcceptCharset):
    """
    Represent when an ``Accept-Charset`` header is invalid or not in request.

    This is the base class for the behaviour that
    :class:`.AcceptCharsetInvalidHeader` and :class:`.AcceptCharsetNoHeader`
    have in common.

    :rfc:`7231` does not provide any guidance on what should happen if the
    ``Accept-Charset`` header has an invalid value. This implementation
    disregards the header when the header is invalid, so
    :class:`.AcceptCharsetInvalidHeader` and :class:`.AcceptCharsetNoHeader`
    have much behaviour in common.
    """

    def __bool__(self):
        """
        Return whether ``self`` represents a valid ``Accept-Charset`` header.

        Return ``True`` if ``self`` represents a valid header, and ``False`` if
        it represents an invalid header, or the header not being in the
        request.

        For this class, it always returns ``False``.
        """
        return False
    __nonzero__ = __bool__  # Python 2

    def __contains__(self, offer):
        """
        Return ``bool`` indicating whether `offer` is acceptable.

        .. warning::

           The behavior of ``.__contains__`` for the ``AcceptCharset`` classes
           is currently being maintained for backward compatibility, but it
           will change in the future to better conform to the RFC.

        :param offer: (``str``) charset offer
        :return: (``bool``) Whether ``offer`` is acceptable according to the
                 header.

        For this class, either there is no ``Accept-Charset`` header in the
        request, or the header is invalid, so any charset is acceptable, and
        this always returns ``True``.
        """
        warnings.warn(
            'The behavior of .__contains__ for the AcceptCharset classes is '
            'currently being maintained for backward compatibility, but it '
            'will change in the future to better conform to the RFC.',
            DeprecationWarning,
        )
        return True

    def __iter__(self):
        """
        Return all the items with non-0 qvalues, in order of preference.

        .. warning::

           The behavior of this method is currently maintained for backward
           compatibility, but will change in the future.

        :return: iterator of all the items (charset or ``*``) in the header
                 with non-0 qvalues, in descending order of qvalue. If two
                 items have the same qvalue, they are returned in the order of
                 their positions in the header, from left to right.

        When there is no ``Accept-Charset`` header in the request or the header
        is invalid, there are no items, and this always returns an empty
        iterator.
        """
        warnings.warn(
            'The behavior of AcceptCharsetValidHeader.__iter__ is currently '
            'maintained for backward compatibility, but will change in the '
            'future.',
            DeprecationWarning,
        )
        return iter(())

    def acceptable_offers(self, offers):
        """
        Return the offers that are acceptable according to the header.

        The offers are returned in descending order of preference, where
        preference is indicated by the qvalue of the charset or ``*`` in the
        header matching the offer.

        This uses the matching rules described in :rfc:`RFC 7231, section 5.3.3
        <7231#section-5.3.3>`.

        :param offers: ``iterable`` of ``str`` charsets
        :return: A list of tuples of the form (charset, qvalue), in descending
                 order of qvalue. Where two offers have the same qvalue, they
                 are returned in the same order as their order in `offers`.

                 | When the header is invalid or there is no ``Accept-Charset``
                   header in the request, all `offers` are considered
                   acceptable, so this method returns a list of (charset,
                   qvalue) tuples where each offer in `offers` is paired with
                   the qvalue of 1.0, in the same order as `offers`.
        """
        return [(offer, 1.0) for offer in offers]

    def best_match(self, offers, default_match=None):
        """
        Return the best match from the sequence of charset `offers`.

        This is the ``.best_match()`` method for when the header is invalid or
        not found in the request, corresponding to
        :meth:`AcceptCharsetValidHeader.best_match`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future (see the documentation for
           :meth:`AcceptCharsetValidHeader.best_match`).

        When the header is invalid, or there is no `Accept-Charset` header in
        the request, all the charsets in `offers` are considered acceptable, so
        the best match is the charset in `offers` with the highest server
        quality value (if the server quality value is not supplied, it is 1).

        If more than one charsets in `offers` have the same highest server
        quality value, then the one that shows up first in `offers` is the best
        match.

        :param offers: (iterable)

                       | Each item in the iterable may be a ``str`` charset, or
                         a (charset, server quality value) ``tuple`` or
                         ``list``.  (The two may be mixed in the iterable.)

        :param default_match: (optional, any type) the value to be returned if
                              `offers` is empty.

        :return: (``str``, or the type of `default_match`)

                 | The charset that has the highest server quality value.  If
                   `offers` is empty, the value of `default_match` is returned.
        """
        warnings.warn(
            'The behavior of .best_match for the AcceptCharset classes is '
            'currently being maintained for backward compatibility, but the '
            'method will be deprecated in the future, as its behavior is not '
            'specified in (and currently does not conform to) RFC 7231.',
            DeprecationWarning,
        )
        best_quality = -1
        best_offer = default_match
        for offer in offers:
            if isinstance(offer, (list, tuple)):
                offer, quality = offer
            else:
                quality = 1
            if quality > best_quality:
                best_offer = offer
                best_quality = quality
        return best_offer

    def quality(self, offer):
        """
        Return quality value of given offer, or ``None`` if there is no match.

        This is the ``.quality()`` method for when the header is invalid or not
        found in the request, corresponding to
        :meth:`AcceptCharsetValidHeader.quality`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future (see the documentation for
           :meth:`AcceptCharsetValidHeader.quality`).

        :param offer: (``str``) charset offer
        :return: (``float``) ``1.0``.

        When the ``Accept-Charset`` header is invalid or not in the request,
        all offers are equally acceptable, so 1.0 is always returned.
        """
        warnings.warn(
            'The behavior of .quality for the Accept-Charset classes is '
            'currently being maintained for backward compatibility, but the '
            'method will be deprecated in the future, as its behavior does not'
            ' conform to RFC 7231.',
            DeprecationWarning,
        )
        return 1.0


class AcceptCharsetNoHeader(_AcceptCharsetInvalidOrNoHeader):
    """
    Represent when there is no ``Accept-Charset`` header in the request.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptCharsetNoHeader.__add__`).
    """

    @property
    def header_value(self):
        """
        (``str`` or ``None``) The header value.

        As there is no header in the request, this is ``None``.
        """
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        As there is no header in the request, this is ``None``.
        """
        return self._parsed

    def __init__(self):
        """
        Create an :class:`AcceptCharsetNoHeader` instance.
        """
        self._header_value = None
        self._parsed = None
        self._parsed_nonzero = None

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, where keys are charsets and values are qvalues
        * a ``tuple`` or ``list``, where each item is a charset ``str`` or a
          ``tuple`` or ``list`` (charset, qvalue) pair (``str``\ s and pairs
          can be mixed within the ``tuple`` or ``list``)
        * an :class:`AcceptCharsetValidHeader`, :class:`AcceptCharsetNoHeader`,
          or :class:`AcceptCharsetInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or an
        :class:`AcceptCharsetValidHeader` instance, a new
        :class:`AcceptCharsetValidHeader` instance with the valid header value
        is returned.

        If `other` is ``None``, an :class:`AcceptCharsetNoHeader` instance, an
        invalid header value, or an :class:`AcceptCharsetInvalidHeader`
        instance, a new :class:`AcceptCharsetNoHeader` instance is returned.
        """
        if isinstance(other, AcceptCharsetValidHeader):
            return AcceptCharsetValidHeader(header_value=other.header_value)

        if isinstance(
            other, (AcceptCharsetNoHeader, AcceptCharsetInvalidHeader)
        ):
            return self.__class__()

        return self._add_instance_and_non_accept_charset_type(
            instance=self, other=other,
        )

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptCharsetNoHeader.__add__`.
        """
        return self.__add__(other=other)

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    def __str__(self):
        """Return the ``str`` ``'<no header in request>'``."""
        return '<no header in request>'

    def _add_instance_and_non_accept_charset_type(self, instance, other):
        if not other:
            return self.__class__()

        other_header_value = self._python_value_to_header_str(value=other)

        try:
            return AcceptCharsetValidHeader(header_value=other_header_value)
        except ValueError:  # invalid header value
            return self.__class__()


class AcceptCharsetInvalidHeader(_AcceptCharsetInvalidOrNoHeader):
    """
    Represent an invalid ``Accept-Charset`` header.

    An invalid header is one that does not conform to
    :rfc:`7231#section-5.3.3`. As specified in the RFC, an empty header is an
    invalid ``Accept-Charset`` header.

    :rfc:`7231` does not provide any guidance on what should happen if the
    ``Accept-Charset`` header has an invalid value. This implementation
    disregards the header, and treats it as if there is no ``Accept-Charset``
    header in the request.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptCharsetInvalidHeader.__add__`).
    """

    @property
    def header_value(self):
        """(``str`` or ``None``) The header value."""
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        As the header is invalid and cannot be parsed, this is ``None``.
        """
        return self._parsed

    def __init__(self, header_value):
        """
        Create an :class:`AcceptCharsetInvalidHeader` instance.
        """
        self._header_value = header_value
        self._parsed = None
        self._parsed_nonzero = None

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, where keys are charsets and values are qvalues
        * a ``tuple`` or ``list``, where each item is a charset ``str`` or a
          ``tuple`` or ``list`` (charset, qvalue) pair (``str``\ s and pairs
          can be mixed within the ``tuple`` or ``list``)
        * an :class:`AcceptCharsetValidHeader`, :class:`AcceptCharsetNoHeader`,
          or :class:`AcceptCharsetInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or an
        :class:`AcceptCharsetValidHeader` instance, a new
        :class:`AcceptCharsetValidHeader` instance with the valid header value
        is returned.

        If `other` is ``None``, an :class:`AcceptCharsetNoHeader` instance, an
        invalid header value, or an :class:`AcceptCharsetInvalidHeader`
        instance, a new :class:`AcceptCharsetNoHeader` instance is returned.
        """
        if isinstance(other, AcceptCharsetValidHeader):
            return AcceptCharsetValidHeader(header_value=other.header_value)

        if isinstance(
            other, (AcceptCharsetNoHeader, AcceptCharsetInvalidHeader)
        ):
            return AcceptCharsetNoHeader()

        return self._add_instance_and_non_accept_charset_type(
            instance=self, other=other,
        )

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptCharsetValidHeader.__add__`.
        """
        return self._add_instance_and_non_accept_charset_type(
            instance=self, other=other, instance_on_the_right=True,
        )

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)
        # We do not display the header_value, as it is untrusted input. The
        # header_value could always be easily obtained from the .header_value
        # property.

    def __str__(self):
        """Return the ``str`` ``'<invalid header value>'``."""
        return '<invalid header value>'

    def _add_instance_and_non_accept_charset_type(
        self, instance, other, instance_on_the_right=False,
    ):
        if not other:
            return AcceptCharsetNoHeader()

        other_header_value = self._python_value_to_header_str(value=other)

        try:
            return AcceptCharsetValidHeader(header_value=other_header_value)
        except ValueError:  # invalid header value
            return AcceptCharsetNoHeader()


def create_accept_charset_header(header_value):
    """
    Create an object representing the ``Accept-Charset`` header in a request.

    :param header_value: (``str``) header value
    :return: If `header_value` is ``None``, an :class:`AcceptCharsetNoHeader`
             instance.

             | If `header_value` is a valid ``Accept-Charset`` header, an
               :class:`AcceptCharsetValidHeader` instance.

             | If `header_value` is an invalid ``Accept-Charset`` header, an
               :class:`AcceptCharsetInvalidHeader` instance.
    """
    if header_value is None:
        return AcceptCharsetNoHeader()
    try:
        return AcceptCharsetValidHeader(header_value=header_value)
    except ValueError:
        return AcceptCharsetInvalidHeader(header_value=header_value)


def accept_charset_property():
    doc = """
        Property representing the ``Accept-Charset`` header.

        (:rfc:`RFC 7231, section 5.3.3 <7231#section-5.3.3>`)

        The header value in the request environ is parsed and a new object
        representing the header is created every time we *get* the value of the
        property. (*set* and *del* change the header value in the request
        environ, and do not involve parsing.)
    """

    ENVIRON_KEY = 'HTTP_ACCEPT_CHARSET'

    def fget(request):
        """Get an object representing the header in the request."""
        return create_accept_charset_header(
            header_value=request.environ.get(ENVIRON_KEY)
        )

    def fset(request, value):
        """
        Set the corresponding key in the request environ.

        `value` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, where keys are charsets and values are qvalues
        * a ``tuple`` or ``list``, where each item is a charset ``str`` or a
          ``tuple`` or ``list`` (charset, qvalue) pair (``str``\ s and pairs
          can be mixed within the ``tuple`` or ``list``)
        * an :class:`AcceptCharsetValidHeader`, :class:`AcceptCharsetNoHeader`,
          or :class:`AcceptCharsetInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``
        """
        if value is None or isinstance(value, AcceptCharsetNoHeader):
            fdel(request=request)
        else:
            if isinstance(
                value, (AcceptCharsetValidHeader, AcceptCharsetInvalidHeader)
            ):
                header_value = value.header_value
            else:
                header_value = AcceptCharset._python_value_to_header_str(
                    value=value,
                )
            request.environ[ENVIRON_KEY] = header_value

    def fdel(request):
        """Delete the corresponding key from the request environ."""
        try:
            del request.environ[ENVIRON_KEY]
        except KeyError:
            pass

    return property(fget, fset, fdel, textwrap.dedent(doc))


class AcceptEncoding(object):
    """
    Represent an ``Accept-Encoding`` header.

    Base class for :class:`AcceptEncodingValidHeader`,
    :class:`AcceptEncodingNoHeader`, and :class:`AcceptEncodingInvalidHeader`.
    """

    # RFC 7231 Section 3.1.2.1 "Content Codings":
    # content-coding = token
    # Section 5.3.4 "Accept-Encoding":
    # Accept-Encoding  = #( codings [ weight ] )
    # codings          = content-coding / "identity" / "*"
    codings_re = token_re
    # "identity" (case-insensitive) and "*" are both already included in token
    # rule
    codings_n_weight_re = _item_n_weight_re(item_re=codings_re)
    codings_n_weight_compiled_re = re.compile(codings_n_weight_re)
    accept_encoding_compiled_re = _list_0_or_more__compiled_re(
        element_re=codings_n_weight_re,
    )

    @classmethod
    def _python_value_to_header_str(cls, value):
        if isinstance(value, str):
            header_str = value
        else:
            if hasattr(value, 'items'):
                value = sorted(
                    value.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            if isinstance(value, (tuple, list)):
                result = []
                for item in value:
                    if isinstance(item, (tuple, list)):
                        item = _item_qvalue_pair_to_header_element(pair=item)
                    result.append(item)
                header_str = ', '.join(result)
            else:
                header_str = str(value)
        return header_str

    @classmethod
    def parse(cls, value):
        """
        Parse an ``Accept-Encoding`` header.

        :param value: (``str``) header value
        :return: If `value` is a valid ``Accept-Encoding`` header, returns an
                 iterator of (codings, quality value) tuples, as parsed from
                 the header from left to right.
        :raises ValueError: if `value` is an invalid header
        """
        # Check if header is valid
        # Using Python stdlib's `re` module, there is currently no way to check
        # the match *and* get all the groups using the same regex, so we have
        # to use one regex to check the match, and another to get the groups.
        if cls.accept_encoding_compiled_re.match(value) is None:
            raise ValueError('Invalid value for an Accept-Encoding header.')
        def generator(value):
            for match in (cls.codings_n_weight_compiled_re.finditer(value)):
                codings = match.group(1)
                qvalue = match.group(2)
                qvalue = float(qvalue) if qvalue else 1.0
                yield (codings, qvalue)
        return generator(value=value)


class AcceptEncodingValidHeader(AcceptEncoding):
    """
    Represent a valid ``Accept-Encoding`` header.

    A valid header is one that conforms to :rfc:`RFC 7231, section 5.3.4
    <7231#section-5.3.4>`.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptEncodingValidHeader.__add__`).
    """

    @property
    def header_value(self):
        """(``str`` or ``None``) The header value."""
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        A list of (*codings*, *qvalue*) tuples, where

        *codings* (``str``) is a content-coding, the string "``identity``", or
        "``*``"; and

        *qvalue* (``float``) is the quality value of the codings.
        """
        return self._parsed

    def __init__(self, header_value):
        """
        Create an :class:`AcceptEncodingValidHeader` instance.

        :param header_value: (``str``) header value.
        :raises ValueError: if `header_value` is an invalid value for an
                            ``Accept-Encoding`` header.
        """
        self._header_value = header_value
        self._parsed = list(self.parse(header_value))
        self._parsed_nonzero = [item for item in self.parsed if item[1]]
        # item[1] is the qvalue

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, with content-coding, ``identity`` or ``*`` ``str``\ s as
          keys, and qvalue ``float``\ s as values
        * a ``tuple`` or ``list``, where each item is either a header element
          ``str``, or a (content-coding/``identity``/``*``, qvalue) ``tuple``
          or ``list``
        * an :class:`AcceptEncodingValidHeader`,
          :class:`AcceptEncodingNoHeader`, or
          :class:`AcceptEncodingInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or another
        :class:`AcceptEncodingValidHeader` instance, and the header value it
        represents is not ``''``, then the two header values are joined with
        ``', '``, and a new :class:`AcceptEncodingValidHeader` instance with
        the new header value is returned.

        If `other` is a valid header value or another
        :class:`AcceptEncodingValidHeader` instance representing a header value
        of ``''``; or if it is ``None`` or an :class:`AcceptEncodingNoHeader`
        instance; or if it is an invalid header value, or an
        :class:`AcceptEncodingInvalidHeader` instance, then a new
        :class:`AcceptEncodingValidHeader` instance with the same header value
        as ``self`` is returned.
        """
        if isinstance(other, AcceptEncodingValidHeader):
            if other.header_value == '':
                return self.__class__(header_value=self.header_value)
            else:
                return create_accept_encoding_header(
                    header_value=self.header_value + ', ' + other.header_value,
                )

        if isinstance(
            other, (AcceptEncodingNoHeader, AcceptEncodingInvalidHeader)
        ):
            return self.__class__(header_value=self.header_value)

        return self._add_instance_and_non_accept_encoding_type(
            instance=self, other=other,
        )

    def __bool__(self):
        """
        Return whether ``self`` represents a valid ``Accept-Encoding`` header.

        Return ``True`` if ``self`` represents a valid header, and ``False`` if
        it represents an invalid header, or the header not being in the
        request.

        For this class, it always returns ``True``.
        """
        return True
    __nonzero__ = __bool__  # Python 2

    def __contains__(self, offer):
        """
        Return ``bool`` indicating whether `offer` is acceptable.

        .. warning::

           The behavior of :meth:`AcceptEncodingValidHeader.__contains__` is
           currently being maintained for backward compatibility, but it will
           change in the future to better conform to the RFC.

        :param offer: (``str``) a content-coding or ``identity`` offer
        :return: (``bool``) Whether ``offer`` is acceptable according to the
                 header.

        The behavior of this method does not fully conform to :rfc:`7231`.
        It does not correctly interpret ``*``::

            >>> 'gzip' in AcceptEncodingValidHeader('gzip;q=0, *')
            True

        and does not handle the ``identity`` token correctly::

            >>> 'identity' in AcceptEncodingValidHeader('gzip')
            False
        """
        warnings.warn(
            'The behavior of AcceptEncodingValidHeader.__contains__ is '
            'currently being maintained for backward compatibility, but it '
            'will change in the future to better conform to the RFC.',
            DeprecationWarning,
        )
        for mask, quality in self._parsed_nonzero:
            if self._old_match(mask, offer):
                return True

    def __iter__(self):
        """
        Return all the ranges with non-0 qvalues, in order of preference.

        .. warning::

           The behavior of this method is currently maintained for backward
           compatibility, but will change in the future.

        :return: iterator of all the (content-coding/``identity``/``*``) items
                 in the header with non-0 qvalues, in descending order of
                 qvalue. If two items have the same qvalue, they are returned
                 in the order of their positions in the header, from left to
                 right.

        Please note that this is a simple filter for the items in the header
        with non-0 qvalues, and is not necessarily the same as what the client
        prefers, e.g. ``'gzip;q=0, *'`` means 'everything but gzip', but
        ``list(instance)`` would return only ``['*']``.
        """
        warnings.warn(
            'The behavior of AcceptEncodingLanguageValidHeader.__iter__ is '
            'currently maintained for backward compatibility, but will change'
            ' in the future.',
            DeprecationWarning,
        )

        for m,q in sorted(
            self._parsed_nonzero,
            key=lambda i: i[1],
            reverse=True
        ):
            yield m

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptEncodingValidHeader.__add__`.
        """
        return self._add_instance_and_non_accept_encoding_type(
            instance=self, other=other, instance_on_the_right=True,
        )

    def __repr__(self):
        return '<{} ({!r})>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        r"""
        Return a tidied up version of the header value.

        e.g. If the ``header_value`` is ``",\t, a ;\t q=0.20 , b ,',"``,
        ``str(instance)`` returns ``"a;q=0.2, b, '"``.
        """
        return ', '.join(
            _item_qvalue_pair_to_header_element(pair=tuple_)
            for tuple_ in self.parsed
        )

    def _add_instance_and_non_accept_encoding_type(
        self, instance, other, instance_on_the_right=False,
    ):
        if not other:
            return self.__class__(header_value=instance.header_value)

        other_header_value = self._python_value_to_header_str(value=other)

        if other_header_value == '':
            # if ``other`` is an object whose type we don't recognise, and
            # str(other) returns ''
            return self.__class__(header_value=instance.header_value)

        try:
            self.parse(value=other_header_value)
        except ValueError:  # invalid header value
            return self.__class__(header_value=instance.header_value)

        new_header_value = (
            (other_header_value + ', ' + instance.header_value)
            if instance_on_the_right
            else (instance.header_value + ', ' + other_header_value)
        )
        return self.__class__(header_value=new_header_value)

    def _old_match(self, mask, offer):
        """
        Return whether content-coding offer matches codings header item.

        .. warning::

           This is maintained for backward compatibility, and will be
           deprecated in the future.

        This method was WebOb's old criterion for deciding whether a
        content-coding offer matches a header item (content-coding,
        ``identity`` or ``*``), used in

        - :meth:`AcceptCharsetValidHeader.__contains__`
        - :meth:`AcceptCharsetValidHeader.best_match`
        - :meth:`AcceptCharsetValidHeader.quality`

        It does not conform to :rfc:`RFC 7231, section 5.3.4
        <7231#section-5.3.4>` in that it does not interpret ``*`` values in the
        header correctly: ``*`` should only match content-codings not mentioned
        elsewhere in the header.
        """
        return mask == '*' or offer.lower() == mask.lower()

    def acceptable_offers(self, offers):
        """
        Return the offers that are acceptable according to the header.

        The offers are returned in descending order of preference, where
        preference is indicated by the qvalue of the item (content-coding,
        "identity" or "*") in the header that matches the offer.

        This uses the matching rules described in :rfc:`RFC 7231, section 5.3.4
        <7231#section-5.3.4>`.

        :param offers: ``iterable`` of ``str``s, where each ``str`` is a
                       content-coding or the string ``identity`` (the token
                       used to represent "no encoding")
        :return: A list of tuples of the form (content-coding or "identity",
                 qvalue), in descending order of qvalue. Where two offers have
                 the same qvalue, they are returned in the same order as their
                 order in `offers`.

        Use the string ``'identity'`` (without the quotes) in `offers` to
        indicate an offer with no content-coding. From the RFC: 'If the
        representation has no content-coding, then it is acceptable by default
        unless specifically excluded by the Accept-Encoding field stating
        either "identity;q=0" or "\*;q=0" without a more specific entry for
        "identity".' The RFC does not specify the qvalue that should be
        assigned to the representation/offer with no content-coding; this
        implementation assigns it a qvalue of 1.0.
        """
        lowercased_parsed = [
            (codings.lower(), qvalue) for (codings, qvalue) in self.parsed
        ]
        lowercased_offers = [offer.lower() for offer in offers]

        not_acceptable_codingss = set()
        acceptable_codingss = dict()
        asterisk_qvalue = None

        for codings, qvalue in lowercased_parsed:
            if codings == '*':
                if asterisk_qvalue is None:
                    asterisk_qvalue = qvalue
            elif (
                codings not in acceptable_codingss and codings not in
                not_acceptable_codingss
                # if we have not already encountered this codings in the header
            ):
                if qvalue == 0.0:
                    not_acceptable_codingss.add(codings)
                else:
                    acceptable_codingss[codings] = qvalue
        acceptable_codingss = list(acceptable_codingss.items())
        # Sort acceptable_codingss by qvalue, descending order
        acceptable_codingss.sort(key=lambda tuple_: tuple_[1], reverse=True)

        filtered_offers = []
        for index, offer in enumerate(lowercased_offers):
            # If offer matches a non-* codings with q=0, it is filtered out
            if any((
                (offer == codings) for codings in not_acceptable_codingss
            )):
                continue

            matched_codings_qvalue = None
            for codings, qvalue in acceptable_codingss:
                if offer == codings:
                    matched_codings_qvalue = qvalue
                    break
            else:
                if asterisk_qvalue:
                    matched_codings_qvalue = asterisk_qvalue
                elif asterisk_qvalue != 0.0 and offer == 'identity':
                    matched_codings_qvalue = 1.0
            if matched_codings_qvalue is not None:  # if there was a match
                filtered_offers.append((
                    offers[index], matched_codings_qvalue, index
                ))

        # sort by position in `offers` argument, ascending
        filtered_offers.sort(key=lambda tuple_: tuple_[2])
        # When qvalues are tied, position in `offers` is the tiebreaker.

        # sort by qvalue, descending
        filtered_offers.sort(key=lambda tuple_: tuple_[1], reverse=True)

        return [(item[0], item[1]) for item in filtered_offers]
        # (offer, qvalue), dropping the position

    def best_match(self, offers, default_match=None):
        """
        Return the best match from the sequence of `offers`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future.

           :meth:`AcceptEncodingValidHeader.best_match` uses its own algorithm
           (one not specified in :rfc:`RFC 7231 <7231>`) to determine what is a
           best match. The algorithm has many issues, and does not conform to
           the RFC.

        Each offer in `offers` is checked against each non-``q=0`` item
        (content-coding/``identity``/``*``) in the header. If the two are a
        match according to WebOb's old criterion for a match, the quality value
        of the match is the qvalue of the item from the header multiplied by
        the server quality value of the offer (if the server quality value is
        not supplied, it is 1).

        The offer in the match with the highest quality value is the best
        match. If there is more than one match with the highest qvalue, the one
        that shows up first in `offers` is the best match.

        :param offers: (iterable)

                       | Each item in the iterable may be a ``str`` *codings*,
                         or a (*codings*, server quality value) ``tuple`` or
                         ``list``, where *codings* is either a content-coding,
                         or the string ``identity`` (which represents *no
                         encoding*). ``str`` and ``tuple``/``list`` elements
                         may be mixed within the iterable.

        :param default_match: (optional, any type) the value to be returned if
                              there is no match

        :return: (``str``, or the type of `default_match`)

                 | The offer that is the best match. If there is no match, the
                   value of `default_match` is returned.

        This method does not conform to :rfc:`RFC 7231, section 5.3.4
        <7231#section-5.3.4>`, in that it does not correctly interpret ``*``::

            >>> AcceptEncodingValidHeader('gzip;q=0, *').best_match(['gzip'])
            'gzip'

        and does not handle the ``identity`` token correctly::

            >>> instance = AcceptEncodingValidHeader('gzip')
            >>> instance.best_match(['identity']) is None
            True
        """
        warnings.warn(
            'The behavior of AcceptEncodingValidHeader.best_match is '
            'currently being maintained for backward compatibility, but it '
            'will be deprecated in the future, as it does not conform to the'
            ' RFC.',
            DeprecationWarning,
        )
        best_quality = -1
        best_offer = default_match
        matched_by = '*/*'
        for offer in offers:
            if isinstance(offer, (tuple, list)):
                offer, server_quality = offer
            else:
                server_quality = 1
            for item in self._parsed_nonzero:
                mask = item[0]
                quality = item[1]
                possible_quality = server_quality * quality
                if possible_quality < best_quality:
                    continue
                elif possible_quality == best_quality:
                    # 'text/plain' overrides 'message/*' overrides '*/*'
                    # (if all match w/ the same q=)
                    # [We can see that this was written for the Accept header,
                    # not the Accept-Encoding header.]
                    if matched_by.count('*') <= mask.count('*'):
                        continue
                if self._old_match(mask, offer):
                    best_quality = possible_quality
                    best_offer = offer
                    matched_by = mask
        return best_offer

    def quality(self, offer):
        """
        Return quality value of given offer, or ``None`` if there is no match.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future.

        :param offer: (``str``) A content-coding, or ``identity``.
        :return: (``float`` or ``None``)

                 | The quality value from the header item
                   (content-coding/``identity``/``*``) that matches the
                   `offer`, or ``None`` if there is no match.

        The behavior of this method does not conform to :rfc:`RFC 7231, section
        5.3.4<7231#section-5.3.4>`, in that it does not correctly interpret
        ``*``::

            >>> AcceptEncodingValidHeader('gzip;q=0, *').quality('gzip')
            1.0

        and does not handle the ``identity`` token correctly::

            >>> AcceptEncodingValidHeader('gzip').quality('identity') is None
            True
        """
        warnings.warn(
            'The behavior of AcceptEncodingValidHeader.quality is currently '
            'being maintained for backward compatibility, but it will be '
            'deprecated in the future, as it does not conform to the RFC.',
            DeprecationWarning,
        )
        bestq = 0
        for mask, q in self.parsed:
            if self._old_match(mask, offer):
                bestq = max(bestq, q)
        return bestq or None


class _AcceptEncodingInvalidOrNoHeader(AcceptEncoding):
    """
    Represent when an ``Accept-Encoding`` header is invalid or not in request.

    This is the base class for the behaviour that
    :class:`.AcceptEncodingInvalidHeader` and :class:`.AcceptEncodingNoHeader`
    have in common.

    :rfc:`7231` does not provide any guidance on what should happen if the
    ``AcceptEncoding`` header has an invalid value. This implementation
    disregards the header when the header is invalid, so
    :class:`.AcceptEncodingInvalidHeader` and :class:`.AcceptEncodingNoHeader`
    have much behaviour in common.
    """

    def __bool__(self):
        """
        Return whether ``self`` represents a valid ``Accept-Encoding`` header.

        Return ``True`` if ``self`` represents a valid header, and ``False`` if
        it represents an invalid header, or the header not being in the
        request.

        For this class, it always returns ``False``.
        """
        return False
    __nonzero__ = __bool__  # Python 2

    def __contains__(self, offer):
        """
        Return ``bool`` indicating whether `offer` is acceptable.

        .. warning::

           The behavior of ``.__contains__`` for the ``Accept-Encoding``
           classes is currently being maintained for backward compatibility,
           but it will change in the future to better conform to the RFC.

        :param offer: (``str``) a content-coding or ``identity`` offer
        :return: (``bool``) Whether ``offer`` is acceptable according to the
                 header.

        For this class, either there is no ``Accept-Encoding`` header in the
        request, or the header is invalid, so any content-coding is acceptable,
        and this always returns ``True``.
        """
        warnings.warn(
            'The behavior of .__contains__ for the Accept-Encoding classes is '
            'currently being maintained for backward compatibility, but it '
            'will change in the future to better conform to the RFC.',
            DeprecationWarning,
        )
        return True

    def __iter__(self):
        """
        Return all the header items with non-0 qvalues, in order of preference.

        .. warning::

           The behavior of this method is currently maintained for backward
           compatibility, but will change in the future.

        :return: iterator of all the (content-coding/``identity``/``*``) items
                 in the header with non-0 qvalues, in descending order of
                 qvalue. If two items have the same qvalue, they are returned
                 in the order of their positions in the header, from left to
                 right.

        When there is no ``Accept-Encoding`` header in the request or the
        header is invalid, there are no items in the header, so this always
        returns an empty iterator.
        """
        warnings.warn(
            'The behavior of AcceptEncodingValidHeader.__iter__ is currently '
            'maintained for backward compatibility, but will change in the '
            'future.',
            DeprecationWarning,
        )
        return iter(())

    def acceptable_offers(self, offers):
        """
        Return the offers that are acceptable according to the header.

        :param offers: ``iterable`` of ``str``s, where each ``str`` is a
                       content-coding or the string ``identity`` (the token
                       used to represent "no encoding")
        :return: When the header is invalid, or there is no ``Accept-Encoding``
                 header in the request, all `offers` are considered acceptable,
                 so this method returns a list of (content-coding or
                 "identity", qvalue) tuples where each offer in `offers` is
                 paired with the qvalue of 1.0, in the same order as in
                 `offers`.
        """
        return [(offer, 1.0) for offer in offers]

    def best_match(self, offers, default_match=None):
        """
        Return the best match from the sequence of `offers`.

        This is the ``.best_match()`` method for when the header is invalid or
        not found in the request, corresponding to
        :meth:`AcceptEncodingValidHeader.best_match`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future (see the documentation for
           :meth:`AcceptEncodingValidHeader.best_match`).

        When the header is invalid, or there is no `Accept-Encoding` header in
        the request, all `offers` are considered acceptable, so the best match
        is the offer in `offers` with the highest server quality value (if the
        server quality value is not supplied for a media type, it is 1).

        If more than one offer in `offers` have the same highest server quality
        value, then the one that shows up first in `offers` is the best match.

        :param offers: (iterable)

                       | Each item in the iterable may be a ``str`` *codings*,
                         or a (*codings*, server quality value) ``tuple`` or
                         ``list``, where *codings* is either a content-coding,
                         or the string ``identity`` (which represents *no
                         encoding*). ``str`` and ``tuple``/``list`` elements
                         may be mixed within the iterable.

        :param default_match: (optional, any type) the value to be returned if
                              `offers` is empty.

        :return: (``str``, or the type of `default_match`)

                 | The offer that has the highest server quality value. If
                   `offers` is empty, the value of `default_match` is returned.
        """
        warnings.warn(
            'The behavior of .best_match for the Accept-Encoding classes is '
            'currently being maintained for backward compatibility, but the '
            'method will be deprecated in the future, as its behavior is not '
            'specified in (and currently does not conform to) RFC 7231.',
            DeprecationWarning,
        )
        best_quality = -1
        best_offer = default_match
        for offer in offers:
            if isinstance(offer, (list, tuple)):
                offer, quality = offer
            else:
                quality = 1
            if quality > best_quality:
                best_offer = offer
                best_quality = quality
        return best_offer

    def quality(self, offer):
        """
        Return quality value of given offer, or ``None`` if there is no match.

        This is the ``.quality()`` method for when the header is invalid or not
        found in the request, corresponding to
        :meth:`AcceptEncodingValidHeader.quality`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future (see the documentation for
           :meth:`AcceptEncodingValidHeader.quality`).

        :param offer: (``str``) A content-coding, or ``identity``.
        :return: (``float``) ``1.0``.

        When the ``Accept-Encoding`` header is invalid or not in the request,
        all offers are equally acceptable, so 1.0 is always returned.
        """
        warnings.warn(
            'The behavior of .quality for the Accept-Encoding classes is '
            'currently being maintained for backward compatibility, but the '
            'method will be deprecated in the future, as its behavior does '
            'not conform to RFC 7231.',
            DeprecationWarning,
        )
        return 1.0


class AcceptEncodingNoHeader(_AcceptEncodingInvalidOrNoHeader):
    """
    Represent when there is no ``Accept-Encoding`` header in the request.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptEncodingNoHeader.__add__`).
    """

    @property
    def header_value(self):
        """
        (``str`` or ``None``) The header value.

        As there is no header in the request, this is ``None``.
        """
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        As there is no header in the request, this is ``None``.
        """
        return self._parsed

    def __init__(self):
        """
        Create an :class:`AcceptEncodingNoHeader` instance.
        """
        self._header_value = None
        self._parsed = None
        self._parsed_nonzero = None

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, with content-coding, ``identity`` or ``*`` ``str``\ s as
          keys, and qvalue ``float``\ s as values
        * a ``tuple`` or ``list``, where each item is either a header element
          ``str``, or a (content-coding/``identity``/``*``, qvalue) ``tuple``
          or ``list``
        * an :class:`AcceptEncodingValidHeader`,
          :class:`AcceptEncodingNoHeader`, or
          :class:`AcceptEncodingInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or an
        :class:`AcceptEncodingValidHeader` instance, a new
        :class:`AcceptEncodingValidHeader` instance with the valid header value
        is returned.

        If `other` is ``None``, an :class:`AcceptEncodingNoHeader` instance, an
        invalid header value, or an :class:`AcceptEncodingInvalidHeader`
        instance, a new :class:`AcceptEncodingNoHeader` instance is returned.
        """
        if isinstance(other, AcceptEncodingValidHeader):
            return AcceptEncodingValidHeader(header_value=other.header_value)

        if isinstance(
            other, (AcceptEncodingNoHeader, AcceptEncodingInvalidHeader)
        ):
            return self.__class__()

        return self._add_instance_and_non_accept_encoding_type(
            instance=self, other=other,
        )

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptEncodingNoHeader.__add__`.
        """
        return self.__add__(other=other)

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    def __str__(self):
        """Return the ``str`` ``'<no header in request>'``."""
        return '<no header in request>'

    def _add_instance_and_non_accept_encoding_type(self, instance, other):
        if other is None:
            return self.__class__()

        other_header_value = self._python_value_to_header_str(value=other)

        try:
            return AcceptEncodingValidHeader(header_value=other_header_value)
        except ValueError:  # invalid header value
            return self.__class__()


class AcceptEncodingInvalidHeader(_AcceptEncodingInvalidOrNoHeader):
    """
    Represent an invalid ``Accept-Encoding`` header.

    An invalid header is one that does not conform to
    :rfc:`7231#section-5.3.4`.

    :rfc:`7231` does not provide any guidance on what should happen if the
    ``Accept-Encoding`` header has an invalid value. This implementation
    disregards the header, and treats it as if there is no ``Accept-Encoding``
    header in the request.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptEncodingInvalidHeader.__add__`).
    """

    @property
    def header_value(self):
        """(``str`` or ``None``) The header value."""
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        As the header is invalid and cannot be parsed, this is ``None``.
        """
        return self._parsed

    def __init__(self, header_value):
        """
        Create an :class:`AcceptEncodingInvalidHeader` instance.
        """
        self._header_value = header_value
        self._parsed = None
        self._parsed_nonzero = None

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, with content-coding, ``identity`` or ``*`` ``str``\ s as
          keys, and qvalue ``float``\ s as values
        * a ``tuple`` or ``list``, where each item is either a header element
          ``str``, or a (content-coding/``identity``/``*``, qvalue) ``tuple``
          or ``list``
        * an :class:`AcceptEncodingValidHeader`,
          :class:`AcceptEncodingNoHeader`, or
          :class:`AcceptEncodingInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or an
        :class:`AcceptEncodingValidHeader` instance, then a new
        :class:`AcceptEncodingValidHeader` instance with the valid header value
        is returned.

        If `other` is ``None``, an :class:`AcceptEncodingNoHeader` instance, an
        invalid header value, or an :class:`AcceptEncodingInvalidHeader`
        instance, a new :class:`AcceptEncodingNoHeader` instance is returned.
        """
        if isinstance(other, AcceptEncodingValidHeader):
            return AcceptEncodingValidHeader(header_value=other.header_value)

        if isinstance(
            other, (AcceptEncodingNoHeader, AcceptEncodingInvalidHeader)
        ):
            return AcceptEncodingNoHeader()

        return self._add_instance_and_non_accept_encoding_type(
            instance=self, other=other,
        )

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptEncodingValidHeader.__add__`.
        """
        return self._add_instance_and_non_accept_encoding_type(
            instance=self, other=other, instance_on_the_right=True,
        )

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)
        # We do not display the header_value, as it is untrusted input. The
        # header_value could always be easily obtained from the .header_value
        # property.

    def __str__(self):
        """Return the ``str`` ``'<invalid header value>'``."""
        return '<invalid header value>'

    def _add_instance_and_non_accept_encoding_type(
        self, instance, other, instance_on_the_right=False,
    ):
        if other is None:
            return AcceptEncodingNoHeader()

        other_header_value = self._python_value_to_header_str(value=other)

        try:
            return AcceptEncodingValidHeader(header_value=other_header_value)
        except ValueError:  # invalid header value
            return AcceptEncodingNoHeader()


def create_accept_encoding_header(header_value):
    """
    Create an object representing the ``Accept-Encoding`` header in a request.

    :param header_value: (``str``) header value
    :return: If `header_value` is ``None``, an :class:`AcceptEncodingNoHeader`
             instance.

             | If `header_value` is a valid ``Accept-Encoding`` header, an
               :class:`AcceptEncodingValidHeader` instance.

             | If `header_value` is an invalid ``Accept-Encoding`` header, an
               :class:`AcceptEncodingInvalidHeader` instance.
    """
    if header_value is None:
        return AcceptEncodingNoHeader()
    try:
        return AcceptEncodingValidHeader(header_value=header_value)
    except ValueError:
        return AcceptEncodingInvalidHeader(header_value=header_value)


def accept_encoding_property():
    doc = """
        Property representing the ``Accept-Encoding`` header.

        (:rfc:`RFC 7231, section 5.3.4 <7231#section-5.3.4>`)

        The header value in the request environ is parsed and a new object
        representing the header is created every time we *get* the value of the
        property. (*set* and *del* change the header value in the request
        environ, and do not involve parsing.)
    """

    ENVIRON_KEY = 'HTTP_ACCEPT_ENCODING'

    def fget(request):
        """Get an object representing the header in the request."""
        return create_accept_encoding_header(
            header_value=request.environ.get(ENVIRON_KEY)
        )

    def fset(request, value):
        """
        Set the corresponding key in the request environ.

        `value` can be:

        * ``None``
        * a ``str`` header value
        * a ``dict``, with content-coding, ``identity`` or ``*`` ``str``\ s as
          keys, and qvalue ``float``\ s as values
        * a ``tuple`` or ``list``, where each item is either a header element
          ``str``, or a (content-coding/``identity``/``*``, qvalue) ``tuple``
          or ``list``
        * an :class:`AcceptEncodingValidHeader`,
          :class:`AcceptEncodingNoHeader`, or
          :class:`AcceptEncodingInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``
        """
        if value is None or isinstance(value, AcceptEncodingNoHeader):
            fdel(request=request)
        else:
            if isinstance(
                value, (AcceptEncodingValidHeader, AcceptEncodingInvalidHeader)
            ):
                header_value = value.header_value
            else:
                header_value = AcceptEncoding._python_value_to_header_str(
                    value=value,
                )
            request.environ[ENVIRON_KEY] = header_value

    def fdel(request):
        """Delete the corresponding key from the request environ."""
        try:
            del request.environ[ENVIRON_KEY]
        except KeyError:
            pass

    return property(fget, fset, fdel, textwrap.dedent(doc))


class AcceptLanguage(object):
    """
    Represent an ``Accept-Language`` header.

    Base class for :class:`AcceptLanguageValidHeader`,
    :class:`AcceptLanguageNoHeader`, and :class:`AcceptLanguageInvalidHeader`.
    """

    # RFC 7231 Section 5.3.5 "Accept-Language":
    # Accept-Language = 1#( language-range [ weight ] )
    # language-range  =
    #           <language-range, see [RFC4647], Section 2.1>
    # RFC 4647 Section 2.1 "Basic Language Range":
    # language-range   = (1*8ALPHA *("-" 1*8alphanum)) / "*"
    # alphanum         = ALPHA / DIGIT
    lang_range_re = (
        r'\*|'
        '(?:'
        '[A-Za-z]{1,8}'
        '(?:-[A-Za-z0-9]{1,8})*'
        ')'
    )
    lang_range_n_weight_re = _item_n_weight_re(item_re=lang_range_re)
    lang_range_n_weight_compiled_re = re.compile(lang_range_n_weight_re)
    accept_language_compiled_re = _list_1_or_more__compiled_re(
        element_re=lang_range_n_weight_re,
    )

    @classmethod
    def _python_value_to_header_str(cls, value):
        if isinstance(value, str):
            header_str = value
        else:
            if hasattr(value, 'items'):
                value = sorted(
                    value.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            if isinstance(value, (tuple, list)):
                result = []
                for element in value:
                    if isinstance(element, (tuple, list)):
                        element = _item_qvalue_pair_to_header_element(
                            pair=element
                        )
                    result.append(element)
                header_str = ', '.join(result)
            else:
                header_str = str(value)
        return header_str

    @classmethod
    def parse(cls, value):
        """
        Parse an ``Accept-Language`` header.

        :param value: (``str``) header value
        :return: If `value` is a valid ``Accept-Language`` header, returns an
                 iterator of (language range, quality value) tuples, as parsed
                 from the header from left to right.
        :raises ValueError: if `value` is an invalid header
        """
        # Check if header is valid
        # Using Python stdlib's `re` module, there is currently no way to check
        # the match *and* get all the groups using the same regex, so we have
        # to use one regex to check the match, and another to get the groups.
        if cls.accept_language_compiled_re.match(value) is None:
            raise ValueError('Invalid value for an Accept-Language header.')
        def generator(value):
            for match in (
                cls.lang_range_n_weight_compiled_re.finditer(value)
            ):
                lang_range = match.group(1)
                qvalue = match.group(2)
                qvalue = float(qvalue) if qvalue else 1.0
                yield (lang_range, qvalue)
        return generator(value=value)


class AcceptLanguageValidHeader(AcceptLanguage):
    """
    Represent a valid ``Accept-Language`` header.

    A valid header is one that conforms to :rfc:`RFC 7231, section 5.3.5
    <7231#section-5.3.5>`.

    We take the reference from the ``language-range`` syntax rule in :rfc:`RFC
    7231, section 5.3.5 <7231#section-5.3.5>` to :rfc:`RFC 4647, section 2.1
    <4647#section-2.1>` to mean that only basic language ranges (and not
    extended language ranges) are expected in the ``Accept-Language`` header.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptLanguageValidHeader.__add__`).
    """

    def __init__(self, header_value):
        """
        Create an :class:`AcceptLanguageValidHeader` instance.

        :param header_value: (``str``) header value.
        :raises ValueError: if `header_value` is an invalid value for an
                            ``Accept-Language`` header.
        """
        self._header_value = header_value
        self._parsed = list(self.parse(header_value))
        self._parsed_nonzero = [item for item in self.parsed if item[1]]
        # item[1] is the qvalue

    @property
    def header_value(self):
        """(``str`` or ``None``) The header value."""
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        A list of (language range, quality value) tuples.
        """
        return self._parsed

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str``
        * a ``dict``, with language ranges as keys and qvalues as values
        * a ``tuple`` or ``list``, of language range ``str``\ s or of ``tuple``
          or ``list`` (language range, qvalue) pairs (``str``\ s and pairs can
          be mixed within the ``tuple`` or ``list``)
        * an :class:`AcceptLanguageValidHeader`,
          :class:`AcceptLanguageNoHeader`, or
          :class:`AcceptLanguageInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or another
        :class:`AcceptLanguageValidHeader` instance, the two header values are
        joined with ``', '``, and a new :class:`AcceptLanguageValidHeader`
        instance with the new header value is returned.

        If `other` is ``None``, an :class:`AcceptLanguageNoHeader` instance, an
        invalid header value, or an :class:`AcceptLanguageInvalidHeader`
        instance, a new :class:`AcceptLanguageValidHeader` instance with the
        same header value as ``self`` is returned.
        """
        if isinstance(other, AcceptLanguageValidHeader):
            return create_accept_language_header(
                header_value=self.header_value + ', ' + other.header_value,
            )

        if isinstance(
            other, (AcceptLanguageNoHeader, AcceptLanguageInvalidHeader)
        ):
            return self.__class__(header_value=self.header_value)

        return self._add_instance_and_non_accept_language_type(
            instance=self, other=other,
        )

    def __nonzero__(self):
        """
        Return whether ``self`` represents a valid ``Accept-Language`` header.

        Return ``True`` if ``self`` represents a valid header, and ``False`` if
        it represents an invalid header, or the header not being in the
        request.

        For this class, it always returns ``True``.
        """
        return True
    __bool__ = __nonzero__  # Python 3

    def __contains__(self, offer):
        """
        Return ``bool`` indicating whether `offer` is acceptable.

        .. warning::

           The behavior of :meth:`AcceptLanguageValidHeader.__contains__` is
           currently being maintained for backward compatibility, but it will
           change in the future to better conform to the RFC.

           What is 'acceptable' depends on the needs of your application.
           :rfc:`RFC 7231, section 5.3.5 <7231#section-5.3.5>` suggests three
           matching schemes from :rfc:`RFC 4647 <4647>`, two of which WebOb
           supports with :meth:`AcceptLanguageValidHeader.basic_filtering` and
           :meth:`AcceptLanguageValidHeader.lookup` (we interpret the RFC to
           mean that Extended Filtering cannot apply for the
           ``Accept-Language`` header, as the header only accepts basic
           language ranges.) If these are not suitable for the needs of your
           application, you may need to write your own matching using
           :attr:`AcceptLanguageValidHeader.parsed`.

        :param offer: (``str``) language tag offer
        :return: (``bool``) Whether ``offer`` is acceptable according to the
                 header.

        This uses the old criterion of a match in
        :meth:`AcceptLanguageValidHeader._old_match`, which does not conform to
        :rfc:`RFC 7231, section 5.3.5 <7231#section-5.3.5>` or any of the
        matching schemes suggested there. It also does not properly take into
        account ranges with ``q=0`` in the header::

            >>> 'en-gb' in AcceptLanguageValidHeader('en, en-gb;q=0')
            True
            >>> 'en' in AcceptLanguageValidHeader('en;q=0, *')
            True

        (See the docstring for :meth:`AcceptLanguageValidHeader._old_match` for
        other problems with the old criterion for a match.)
        """
        warnings.warn(
            'The behavior of AcceptLanguageValidHeader.__contains__ is '
            'currently being maintained for backward compatibility, but it '
            'will change in the future to better conform to the RFC.',
            DeprecationWarning,
        )
        for mask, quality in self._parsed_nonzero:
            if self._old_match(mask, offer):
                return True
        return False

    def __iter__(self):
        """
        Return all the ranges with non-0 qvalues, in order of preference.

        .. warning::

           The behavior of this method is currently maintained for backward
           compatibility, but will change in the future.

        :return: iterator of all the language ranges in the header with non-0
                 qvalues, in descending order of qvalue. If two ranges have the
                 same qvalue, they are returned in the order of their positions
                 in the header, from left to right.

        Please note that this is a simple filter for the ranges in the header
        with non-0 qvalues, and is not necessarily the same as what the client
        prefers, e.g. ``'en-gb;q=0, *'`` means 'everything but British
        English', but ``list(instance)`` would return only ``['*']``.
        """
        warnings.warn(
            'The behavior of AcceptLanguageValidHeader.__iter__ is currently '
            'maintained for backward compatibility, but will change in the '
            'future.',
            DeprecationWarning,
        )

        for m, q in sorted(
            self._parsed_nonzero,
            key=lambda i: i[1],
            reverse=True
        ):
            yield m

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptLanguageValidHeader.__add__`.
        """
        return self._add_instance_and_non_accept_language_type(
            instance=self, other=other, instance_on_the_right=True,
        )

    def __repr__(self):
        return '<{} ({!r})>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        r"""
        Return a tidied up version of the header value.

        e.g. If the ``header_value`` is ``', \t,de;q=0.000 \t, es;q=1.000, zh,
        jp;q=0.210  ,'``, ``str(instance)`` returns ``'de;q=0, es, zh,
        jp;q=0.21'``.
        """
        return ', '.join(
            _item_qvalue_pair_to_header_element(pair=tuple_)
            for tuple_ in self.parsed
        )

    def _add_instance_and_non_accept_language_type(
        self, instance, other, instance_on_the_right=False,
    ):
        if not other:
            return self.__class__(header_value=instance.header_value)

        other_header_value = self._python_value_to_header_str(value=other)

        try:
            self.parse(value=other_header_value)
        except ValueError:  # invalid header value
            return self.__class__(header_value=instance.header_value)

        new_header_value = (
            (other_header_value + ', ' + instance.header_value)
            if instance_on_the_right
            else (instance.header_value + ', ' + other_header_value)
        )
        return self.__class__(header_value=new_header_value)

    def _old_match(self, mask, item):
        """
        Return whether a language tag matches a language range.

        .. warning::

           This is maintained for backward compatibility, and will be
           deprecated in the future.

        This method was WebOb's old criterion for deciding whether a language
        tag matches a language range, used in

        - :meth:`AcceptLanguageValidHeader.__contains__`
        - :meth:`AcceptLanguageValidHeader.best_match`
        - :meth:`AcceptLanguageValidHeader.quality`

        It does not conform to :rfc:`RFC 7231, section 5.3.5
        <7231#section-5.3.5>`, or any of the matching schemes suggested there.

        :param mask: (``str``)

                     | language range

        :param item: (``str``)

                     | language tag. Subtags in language tags are separated by
                       ``-`` (hyphen). If there are underscores (``_``) in this
                       argument, they will be converted to hyphens before
                       checking the match.

        :return: (``bool``) whether the tag in `item` matches the range in
                 `mask`.

        `mask` and `item` are a match if:

        - ``mask == *``.
        - ``mask == item``.
        - If the first subtag of `item` equals `mask`, or if the first subtag
          of `mask` equals `item`.
          This means that::

              >>> instance._old_match(mask='en-gb', item='en')
              True
              >>> instance._old_match(mask='en', item='en-gb')
              True

          Which is different from any of the matching schemes suggested in
          :rfc:`RFC 7231, section 5.3.5 <7231#section-5.3.5>`, in that none of
          those schemes match both more *and* less specific tags.

          However, this method appears to be only designed for language tags
          and ranges with at most two subtags. So with an `item`/language tag
          with more than two subtags like ``zh-Hans-CN``::

              >>> instance._old_match(mask='zh', item='zh-Hans-CN')
              True
              >>> instance._old_match(mask='zh-Hans', item='zh-Hans-CN')
              False

          From commit history, this does not appear to have been from a
          decision to match only the first subtag, but rather because only
          language ranges and tags with at most two subtags were expected.
        """
        item = item.replace('_', '-').lower()
        mask = mask.lower()
        return (mask == '*'
            or item == mask
            or item.split('-')[0] == mask
            or item == mask.split('-')[0]
        )

    def basic_filtering(self, language_tags):
        """
        Return the tags that match the header, using Basic Filtering.

        This is an implementation of the Basic Filtering matching scheme,
        suggested as a matching scheme for the ``Accept-Language`` header in
        :rfc:`RFC 7231, section 5.3.5 <7231#section-5.3.5>`, and defined in
        :rfc:`RFC 4647, section 3.3.1 <4647#section-3.3.1>`. It filters the
        tags in the `language_tags` argument and returns the ones that match
        the header according to the matching scheme.

        :param language_tags: (``iterable``) language tags
        :return: A list of tuples of the form (language tag, qvalue), in
                 descending order of qvalue. If two or more tags have the same
                 qvalue, they are returned in the same order as that in the
                 header of the ranges they matched. If the matched range is the
                 same for two or more tags (i.e. their matched ranges have the
                 same qvalue and the same position in the header), then they
                 are returned in the same order as that in the `language_tags`
                 argument. If `language_tags` is unordered, e.g. if it is a set
                 or a dict, then that order may not be reliable.

        For each tag in `language_tags`:

        1. If the tag matches a non-``*`` language range in the header with
           ``q=0`` (meaning "not acceptable", see :rfc:`RFC 7231, section 5.3.1
           <7231#section-5.3.1>`), the tag is filtered out.
        2. The non-``*`` language ranges in the header that do not have ``q=0``
           are considered in descending order of qvalue; where two or more
           language ranges have the same qvalue, they are considered in the
           order in which they appear in the header.
        3. A language range 'matches a particular language tag if, in a
           case-insensitive comparison, it exactly equals the tag, or if it
           exactly equals a prefix of the tag such that the first character
           following the prefix is "-".' (:rfc:`RFC 4647, section 3.3.1
           <4647#section-3.3.1>`)
        4. If the tag does not match any of the non-``*`` language ranges, and
           there is a ``*`` language range in the header, then if the ``*``
           language range has ``q=0``, the language tag is filtered out,
           otherwise the tag is considered a match.

        (If a range (``*`` or non-``*``) appears in the header more than once
        -- this would not make sense, but is nonetheless a valid header
        according to the RFC -- the first in the header is used for matching,
        and the others are ignored.)
        """
        # The Basic Filtering matching scheme as applied to the Accept-Language
        # header is very under-specified by RFCs 7231 and 4647. This
        # implementation combines the description of the matching scheme in RFC
        # 4647 and the rules of the Accept-Language header in RFC 7231 to
        # arrive at an algorithm for Basic Filtering as applied to the
        # Accept-Language header.

        lowercased_parsed = [
            (range_.lower(), qvalue) for (range_, qvalue) in self.parsed
        ]
        lowercased_tags = [tag.lower() for tag in language_tags]

        not_acceptable_ranges = set()
        acceptable_ranges = dict()
        asterisk_qvalue = None

        for position_in_header, (range_, qvalue) in enumerate(
            lowercased_parsed
        ):
            if range_ == '*':
                if asterisk_qvalue is None:
                    asterisk_qvalue = qvalue
                    asterisk_position = position_in_header
            elif (
                range_ not in acceptable_ranges and range_ not in
                not_acceptable_ranges
                # if we have not already encountered this range in the header
            ):
                if qvalue == 0.0:
                    not_acceptable_ranges.add(range_)
                else:
                    acceptable_ranges[range_] = (qvalue, position_in_header)
        acceptable_ranges = [
            (range_, qvalue, position_in_header)
            for range_, (qvalue, position_in_header)
            in acceptable_ranges.items()
        ]
        # Sort acceptable_ranges by position_in_header, ascending order
        acceptable_ranges.sort(key=lambda tuple_: tuple_[2])
        # Sort acceptable_ranges by qvalue, descending order
        acceptable_ranges.sort(key=lambda tuple_: tuple_[1], reverse=True)
        # Sort guaranteed to be stable with Python >= 2.2, so position in
        # header is tiebreaker when two ranges have the same qvalue

        def match(tag, range_):
            # RFC 4647, section 2.1: 'A language range matches a particular
            # language tag if, in a case-insensitive comparison, it exactly
            # equals the tag, or if it exactly equals a prefix of the tag such
            # that the first character following the prefix is "-".'
            return (tag == range_) or tag.startswith(range_ + '-')
            # We can assume here that the language tags are valid tags, so we
            # do not have to worry about them being malformed and ending with
            # '-'.

        filtered_tags = []
        for index, tag in enumerate(lowercased_tags):
            # If tag matches a non-* range with q=0, it is filtered out
            if any((
                match(tag=tag, range_=range_)
                for range_ in not_acceptable_ranges
            )):
                continue

            matched_range_qvalue = None
            for range_, qvalue, position_in_header in acceptable_ranges:
                # acceptable_ranges is in descending order of qvalue, and tied
                # ranges are in ascending order of position_in_header, so the
                # first range_ that matches the tag is the best match
                if match(tag=tag, range_=range_):
                    matched_range_qvalue = qvalue
                    matched_range_position = position_in_header
                    break
            else:
                if asterisk_qvalue:
                    # From RFC 4647, section 3.3.1: '...HTTP/1.1 [RFC2616]
                    # specifies that the range "*" matches only languages not
                    # matched by any other range within an "Accept-Language"
                    # header.' (Though RFC 2616 is obsolete, and there is no
                    # mention of the meaning of "*" in RFC 7231, as the
                    # ``language-range`` syntax rule in RFC 7231 section 5.3.1
                    # directs us to RFC 4647, we can only assume that the
                    # meaning of "*" in the Accept-Language header remains the
                    # same).
                    matched_range_qvalue = asterisk_qvalue
                    matched_range_position = asterisk_position
            if matched_range_qvalue is not None:  # if there was a match
                filtered_tags.append((
                    language_tags[index], matched_range_qvalue,
                    matched_range_position
                ))

        # sort by matched_range_position, ascending
        filtered_tags.sort(key=lambda tuple_: tuple_[2])
        # When qvalues are tied, matched range position in the header is the
        # tiebreaker.

        # sort by qvalue, descending
        filtered_tags.sort(key=lambda tuple_: tuple_[1], reverse=True)

        return [(item[0], item[1]) for item in filtered_tags]
        # (tag, qvalue), dropping the matched_range_position

        # We return a list of tuples with qvalues, instead of just a set or
        # a list of language tags, because
        # RFC 4647 section 3.3: "If the language priority list contains more
        # than one range, the content returned is typically ordered in
        # descending level of preference, but it MAY be unordered, according to
        # the needs of the application or protocol."
        # We return the filtered tags in order of preference, each paired with
        # the qvalue of the range that was their best match, as the ordering
        # and the qvalues may well be needed in some applications, and a simple
        # set or list of language tags can always be easily obtained from the
        # returned list if the qvalues are not required. One use for qvalues,
        # for example, would be to indicate that two tags are equally preferred
        # (same qvalue), which we would not be able to do easily with a set or
        # a list without e.g. making a member of the set or list a sequence.

    def best_match(self, offers, default_match=None):
        """
        Return the best match from the sequence of language tag `offers`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future.

           :meth:`AcceptLanguageValidHeader.best_match` uses its own algorithm
           (one not specified in :rfc:`RFC 7231 <7231>`) to determine what is a
           best match. The algorithm has many issues, and does not conform to
           :rfc:`RFC 7231 <7231>`.

           :meth:`AcceptLanguageValidHeader.lookup` is a possible alternative
           for finding a best match -- it conforms to, and is suggested as a
           matching scheme for the ``Accept-Language`` header in, :rfc:`RFC
           7231, section 5.3.5 <7231#section-5.3.5>` -- but please be aware
           that there are differences in how it determines what is a best
           match. If that is not suitable for the needs of your application,
           you may need to write your own matching using
           :attr:`AcceptLanguageValidHeader.parsed`.

        Each language tag in `offers` is checked against each non-0 range in
        the header. If the two are a match according to WebOb's old criterion
        for a match, the quality value of the match is the qvalue of the
        language range from the header multiplied by the server quality value
        of the offer (if the server quality value is not supplied, it is 1).

        The offer in the match with the highest quality value is the best
        match. If there is more than one match with the highest qvalue, the
        match where the language range has a lower number of '*'s is the best
        match. If the two have the same number of '*'s, the one that shows up
        first in `offers` is the best match.

        :param offers: (iterable)

                       | Each item in the iterable may be a ``str`` language
                         tag, or a (language tag, server quality value)
                         ``tuple`` or ``list``. (The two may be mixed in the
                         iterable.)

        :param default_match: (optional, any type) the value to be returned if
                              there is no match

        :return: (``str``, or the type of `default_match`)

                 | The language tag that is the best match. If there is no
                   match, the value of `default_match` is returned.


        **Issues**:

        - Incorrect tiebreaking when quality values of two matches are the same
          (https://github.com/Pylons/webob/issues/256)::

              >>> header = AcceptLanguageValidHeader(
              ...     header_value='en-gb;q=1, en;q=0.8'
              ... )
              >>> header.best_match(offers=['en', 'en-GB'])
              'en'
              >>> header.best_match(offers=['en-GB', 'en'])
              'en-GB'

              >>> header = AcceptLanguageValidHeader(header_value='en-gb, en')
              >>> header.best_match(offers=['en', 'en-gb'])
              'en'
              >>> header.best_match(offers=['en-gb', 'en'])
              'en-gb'

        - Incorrect handling of ``q=0``::

              >>> header = AcceptLanguageValidHeader(header_value='en;q=0, *')
              >>> header.best_match(offers=['en'])
              'en'

              >>> header = AcceptLanguageValidHeader(header_value='fr, en;q=0')
              >>> header.best_match(offers=['en-gb'], default_match='en')
              'en'

        - Matching only takes into account the first subtag when matching a
          range with more specific or less specific tags::

              >>> header = AcceptLanguageValidHeader(header_value='zh')
              >>> header.best_match(offers=['zh-Hans-CN'])
              'zh-Hans-CN'
              >>> header = AcceptLanguageValidHeader(header_value='zh-Hans')
              >>> header.best_match(offers=['zh-Hans-CN'])
              >>> header.best_match(offers=['zh-Hans-CN']) is None
              True

              >>> header = AcceptLanguageValidHeader(header_value='zh-Hans-CN')
              >>> header.best_match(offers=['zh'])
              'zh'
              >>> header.best_match(offers=['zh-Hans'])
              >>> header.best_match(offers=['zh-Hans']) is None
              True

        """
        warnings.warn(
            'The behavior of AcceptLanguageValidHeader.best_match is '
            'currently being maintained for backward compatibility, but it '
            'will be deprecated in the future as it does not conform to the '
            'RFC.',
            DeprecationWarning,
        )
        best_quality = -1
        best_offer = default_match
        matched_by = '*/*'
        # [We can see that this was written for the ``Accept`` header and not
        # the ``Accept-Language`` header, as there are no '/'s in a valid
        # ``Accept-Language`` header.]
        for offer in offers:
            if isinstance(offer, (tuple, list)):
                offer, server_quality = offer
            else:
                server_quality = 1
            for mask, quality in self._parsed_nonzero:
                possible_quality = server_quality * quality
                if possible_quality < best_quality:
                    continue
                elif possible_quality == best_quality:
                    # 'text/plain' overrides 'message/*' overrides '*/*'
                    # (if all match w/ the same q=)
                    if matched_by.count('*') <= mask.count('*'):
                        continue
                    # [This tiebreaking was written for the `Accept` header. A
                    # basic language range in a valid ``Accept-Language``
                    # header can only be either '*' or a range with no '*' in
                    # it. This happens to work here, but is not sufficient as a
                    # tiebreaker.
                    #
                    # A best match here, given this algorithm uses
                    # self._old_match() which matches both more *and* less
                    # specific tags, should be the match where the absolute
                    # value of the difference between the subtag counts of
                    # `mask` and `offer` is the lowest.]
                if self._old_match(mask, offer):
                    best_quality = possible_quality
                    best_offer = offer
                    matched_by = mask
        return best_offer

    def lookup(
        self, language_tags, default_range=None, default_tag=None,
        default=None,
    ):
        """
        Return the language tag that best matches the header, using Lookup.

        This is an implementation of the Lookup matching scheme,
        suggested as a matching scheme for the ``Accept-Language`` header in
        :rfc:`RFC 7231, section 5.3.5 <7231#section-5.3.5>`, and described in
        :rfc:`RFC 4647, section 3.4 <4647#section-3.4>`.

        Each language range in the header is considered in turn, by descending
        order of qvalue; where qvalues are tied, ranges are considered from
        left to right.

        Each language range in the header represents the most specific tag that
        is an acceptable match: Lookup progressively truncates subtags from the
        end of the range until a matching language tag is found. An example is
        given in :rfc:`RFC 4647, section 3.4 <4647#section-3.4>`, under
        "Example of a Lookup Fallback Pattern":

        ::

            Range to match: zh-Hant-CN-x-private1-private2
            1. zh-Hant-CN-x-private1-private2
            2. zh-Hant-CN-x-private1
            3. zh-Hant-CN
            4. zh-Hant
            5. zh
            6. (default)

        :param language_tags: (``iterable``) language tags

        :param default_range: (optional, ``None`` or ``str``)

                              | If Lookup finds no match using the ranges in
                                the header, and this argument is not None,
                                Lookup will next attempt to match the range in
                                this argument, using the same subtag
                                truncation.

                              | `default_range` cannot be '*', as '*' is
                                skipped in Lookup. See :ref:`note
                                <acceptparse-lookup-asterisk-note>`.

                              | This parameter corresponds to the functionality
                                described in :rfc:`RFC 4647, section 3.4.1
                                <4647#section-3.4.1>`, in the paragraph
                                starting with "One common way to provide for a
                                default is to allow a specific language range
                                to be set as the default..."

        :param default_tag: (optional, ``None`` or ``str``)

                            | At least one of `default_tag` or `default` must
                              be supplied as an argument to the method, to
                              define the defaulting behaviour.

                            | If Lookup finds no match using the ranges in the
                              header and `default_range`, this argument is not
                              ``None``, and it does not match any range in the
                              header with ``q=0`` (exactly, with no subtag
                              truncation), then this value is returned.

                            | This parameter corresponds to "return a
                              particular language tag designated for the
                              operation", one of the examples of "defaulting
                              behavior" described in :rfc:`RFC 4647, section
                              3.4.1 <4647#section-3.4.1>`.

        :param default: (optional, ``None`` or any type, including a callable)

                        | At least one of `default_tag` or `default` must be
                          supplied as an argument to the method, to define the
                          defaulting behaviour.

                        | If Lookup finds no match using the ranges in the
                          header and `default_range`, and `default_tag` is
                          ``None`` or not acceptable because it matches a
                          ``q=0`` range in the header, then Lookup will next
                          examine the `default` argument.

                        | If `default` is a callable, it will be called, and
                          the callable's return value will be returned.

                        | If `default` is not a callable, the value itself will
                          be returned.

                        | The difference between supplying a ``str`` to
                          `default_tag` and `default` is that `default_tag` is
                          checked against ``q=0`` ranges in the header to see
                          if it matches one of the ranges specified as not
                          acceptable, whereas a ``str`` for the `default`
                          argument is simply returned.

                        | This parameter corresponds to the "defaulting
                          behavior" described in :rfc:`RFC 4647, section 3.4.1
                          <4647#section-3.4.1>`

        :return: (``str``, ``None``, or any type)

                 | The best match according to the Lookup matching scheme, or a
                   return value from one of the default arguments.

        **Notes**:

        .. _acceptparse-lookup-asterisk-note:

        - Lookup's behaviour with '*' language ranges in the header may be
          surprising. From :rfc:`RFC 4647, section 3.4 <4647#section-3.4>`:

              In the lookup scheme, this range does not convey enough
              information by itself to determine which language tag is most
              appropriate, since it matches everything.  If the language range
              "*" is followed by other language ranges, it is skipped.  If the
              language range "*" is the only one in the language priority list
              or if no other language range follows, the default value is
              computed and returned.

          So

          ::

              >>> header = AcceptLanguageValidHeader('de, zh, *')
              >>> header.lookup(language_tags=['ja', 'en'], default='default')
              'default'

        - Any tags in `language_tags` and `default_tag` and any tag matched
          during the subtag truncation search for `default_range`, that are an
          exact match for a non-``*`` range with ``q=0`` in the header, are
          considered not acceptable and ruled out.

        - If there is a ``*;q=0`` in the header, then `default_range` and
          `default_tag` have no effect, as ``*;q=0`` means that all languages
          not already matched by other ranges within the header are
          unacceptable.
        """
        if default_tag is None and default is None:
            raise TypeError(
                '`default_tag` and `default` arguments cannot both be None.'
            )

        # We need separate `default_tag` and `default` arguments because if we
        # only had the `default` argument, there would be no way to tell
        # whether a str is a language tag (in which case we have to check
        # whether it has been specified as not acceptable with a q=0 range in
        # the header) or not (in which case we can just return the value).

        if default_range == '*':
            raise ValueError('default_range cannot be *.')

        parsed = list(self.parsed)

        tags = language_tags
        not_acceptable_ranges = []
        acceptable_ranges = []

        asterisk_non0_found = False
        # Whether there is a '*' range in the header with q={not 0}

        asterisk_q0_found = False
        # Whether there is a '*' range in the header with q=0
        # While '*' is skipped in Lookup because it "does not convey enough
        # information by itself to determine which language tag is most
        # appropriate" (RFC 4647, section 3.4), '*;q=0' is clear in meaning:
        # languages not matched by any other range within the header are not
        # acceptable.

        for range_, qvalue in parsed:
            if qvalue == 0.0:
                if range_ == '*':  # *;q=0
                    asterisk_q0_found = True
                else:  # {non-* range};q=0
                    not_acceptable_ranges.append(range_.lower())
            elif not asterisk_q0_found and range_ == '*':  # *;q={not 0}
                asterisk_non0_found = True
                # if asterisk_q0_found, then it does not matter whether
                # asterisk_non0_found
            else:  # {non-* range};q={not 0}
                acceptable_ranges.append((range_, qvalue))
        # Sort acceptable_ranges by qvalue, descending order
        acceptable_ranges.sort(key=lambda tuple_: tuple_[1], reverse=True)
        # Sort guaranteed to be stable with Python >= 2.2, so position in
        # header is tiebreaker when two ranges have the same qvalue

        acceptable_ranges = [tuple_[0] for tuple_ in acceptable_ranges]
        lowered_tags = [tag.lower() for tag in tags]

        def best_match(range_):
            subtags = range_.split('-')
            while True:
                for index, tag in enumerate(lowered_tags):
                    if tag in not_acceptable_ranges:
                        continue
                        # We think a non-'*' range with q=0 represents only
                        # itself as a tag, and there should be no falling back
                        # with subtag truncation. For example, with
                        # 'en-gb;q=0', it should not mean 'en;q=0': the client
                        # is unlikely to expect that specifying 'en-gb' as not
                        # acceptable would mean that 'en' is also not
                        # acceptable. There is no guidance on this at all in
                        # the RFCs, so it is left to us to decide how it should
                        # work.

                    if tag == range_:
                        return tags[index]  # return the pre-lowered tag

                try:
                    subtag_before_this = subtags[-2]
                except IndexError:  # len(subtags) == 1
                    break
                # len(subtags) >= 2
                if len(subtag_before_this) == 1 and (
                    subtag_before_this.isdigit() or
                    subtag_before_this.isalpha()
                ):  # if subtag_before_this is a single-letter or -digit subtag
                    subtags.pop(-1)  # pop twice instead of once
                subtags.pop(-1)
                range_ = '-'.join(subtags)

        for range_ in acceptable_ranges:
            match = best_match(range_=range_.lower())
            if match is not None:
                return match

        if not asterisk_q0_found:
            if default_range is not None:
                lowered_default_range = default_range.lower()
                match = best_match(range_=lowered_default_range)
                if match is not None:
                    return match

            if default_tag is not None:
                lowered_default_tag = default_tag.lower()
                if lowered_default_tag not in not_acceptable_ranges:
                    return default_tag

        try:
            return default()
        except TypeError:  # default is not a callable
            return default

    def quality(self, offer):
        """
        Return quality value of given offer, or ``None`` if there is no match.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future.

           :meth:`AcceptLanguageValidHeader.quality` uses its own algorithm
           (one not specified in :rfc:`RFC 7231 <7231>`) to determine what is a
           best match. The algorithm has many issues, and does not conform to
           :rfc:`RFC 7231 <7231>`.

           What should be considered a match depends on the needs of your
           application (for example, should a language range in the header
           match a more specific language tag offer, or a less specific tag
           offer?) :rfc:`RFC 7231, section 5.3.5 <7231#section-5.3.5>` suggests
           three matching schemes from :rfc:`RFC 4647 <4647>`, two of which
           WebOb supports with
           :meth:`AcceptLanguageValidHeader.basic_filtering` and
           :meth:`AcceptLanguageValidHeader.lookup` (we interpret the RFC to
           mean that Extended Filtering cannot apply for the
           ``Accept-Language`` header, as the header only accepts basic
           language ranges.) :meth:`AcceptLanguageValidHeader.basic_filtering`
           returns quality values with the matched language tags.
           :meth:`AcceptLanguageValidHeader.lookup` returns a language tag
           without the quality value, but the quality value is less likely to
           be useful when we are looking for a best match.

           If these are not suitable or sufficient for the needs of your
           application, you may need to write your own matching using
           :attr:`AcceptLanguageValidHeader.parsed`.

        :param offer: (``str``) language tag offer
        :return: (``float`` or ``None``)

                 | The highest quality value from the language range(s) that
                   match the `offer`, or ``None`` if there is no match.


        **Issues**:

        - Incorrect handling of ``q=0`` and ``*``::

              >>> header = AcceptLanguageValidHeader(header_value='en;q=0, *')
              >>> header.quality(offer='en')
              1.0

        - Matching only takes into account the first subtag when matching a
          range with more specific or less specific tags::

              >>> header = AcceptLanguageValidHeader(header_value='zh')
              >>> header.quality(offer='zh-Hans-CN')
              1.0
              >>> header = AcceptLanguageValidHeader(header_value='zh-Hans')
              >>> header.quality(offer='zh-Hans-CN')
              >>> header.quality(offer='zh-Hans-CN') is None
              True

              >>> header = AcceptLanguageValidHeader(header_value='zh-Hans-CN')
              >>> header.quality(offer='zh')
              1.0
              >>> header.quality(offer='zh-Hans')
              >>> header.quality(offer='zh-Hans') is None
              True

        """
        warnings.warn(
            'The behavior of AcceptLanguageValidHeader.quality is'
            'currently being maintained for backward compatibility, but it '
            'will be deprecated in the future as it does not conform to the '
            'RFC.',
            DeprecationWarning,
        )
        bestq = 0
        for mask, q in self.parsed:
            if self._old_match(mask, offer):
                bestq = max(bestq, q)
        return bestq or None


class _AcceptLanguageInvalidOrNoHeader(AcceptLanguage):
    """
    Represent when an ``Accept-Language`` header is invalid or not in request.

    This is the base class for the behaviour that
    :class:`.AcceptLanguageInvalidHeader` and :class:`.AcceptLanguageNoHeader`
    have in common.

    :rfc:`7231` does not provide any guidance on what should happen if the
    ``Accept-Language`` header has an invalid value. This implementation
    disregards the header when the header is invalid, so
    :class:`.AcceptLanguageInvalidHeader` and :class:`.AcceptLanguageNoHeader`
    have much behaviour in common.
    """

    def __nonzero__(self):
        """
        Return whether ``self`` represents a valid ``Accept-Language`` header.

        Return ``True`` if ``self`` represents a valid header, and ``False`` if
        it represents an invalid header, or the header not being in the
        request.

        For this class, it always returns ``False``.
        """
        return False
    __bool__ = __nonzero__  # Python 3

    def __contains__(self, offer):
        """
        Return ``bool`` indicating whether `offer` is acceptable.

        .. warning::

           The behavior of ``.__contains__`` for the ``AcceptLanguage`` classes
           is currently being maintained for backward compatibility, but it
           will change in the future to better conform to the RFC.

        :param offer: (``str``) language tag offer
        :return: (``bool``) Whether ``offer`` is acceptable according to the
                 header.

        For this class, either there is no ``Accept-Language`` header in the
        request, or the header is invalid, so any language tag is acceptable,
        and this always returns ``True``.
        """
        warnings.warn(
            'The behavior of .__contains__ for the AcceptLanguage classes is '
            'currently being maintained for backward compatibility, but it '
            'will change in the future to better conform to the RFC.',
            DeprecationWarning,
        )
        return True

    def __iter__(self):
        """
        Return all the ranges with non-0 qvalues, in order of preference.

        .. warning::

           The behavior of this method is currently maintained for backward
           compatibility, but will change in the future.

        :return: iterator of all the language ranges in the header with non-0
                 qvalues, in descending order of qvalue. If two ranges have the
                 same qvalue, they are returned in the order of their positions
                 in the header, from left to right.

        For this class, either there is no ``Accept-Language`` header in the
        request, or the header is invalid, so there are no language ranges, and
        this always returns an empty iterator.
        """
        warnings.warn(
            'The behavior of AcceptLanguageValidHeader.__iter__ is currently '
            'maintained for backward compatibility, but will change in the '
            'future.',
            DeprecationWarning,
        )
        return iter(())

    def basic_filtering(self, language_tags):
        """
        Return the tags that match the header, using Basic Filtering.

        :param language_tags: (``iterable``) language tags
        :return: A list of tuples of the form (language tag, qvalue), in
                 descending order of preference.

        When the header is invalid and when the header is not in the request,
        there are no matches, so this method always returns an empty list.
        """
        return []

    def best_match(self, offers, default_match=None):
        """
        Return the best match from the sequence of language tag `offers`.

        This is the ``.best_match()`` method for when the header is invalid or
        not found in the request, corresponding to
        :meth:`AcceptLanguageValidHeader.best_match`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future (see the documentation for
           :meth:`AcceptLanguageValidHeader.best_match`).

        When the header is invalid, or there is no `Accept-Language` header in
        the request, any of the language tags in `offers` are considered
        acceptable, so the best match is the tag in `offers` with the highest
        server quality value (if the server quality value is not supplied, it
        is 1).

        If more than one language tags in `offers` have the same highest server
        quality value, then the one that shows up first in `offers` is the best
        match.

        :param offers: (iterable)

                       | Each item in the iterable may be a ``str`` language
                         tag, or a (language tag, server quality value)
                         ``tuple`` or ``list``. (The two may be mixed in the
                         iterable.)

        :param default_match: (optional, any type) the value to be returned if
                              `offers` is empty.

        :return: (``str``, or the type of `default_match`)

                 | The language tag that has the highest server quality value.
                   If `offers` is empty, the value of `default_match` is
                   returned.
        """
        warnings.warn(
            'The behavior of .best_match for the AcceptLanguage classes is '
            'currently being maintained for backward compatibility, but the '
            'method will be deprecated in the future, as its behavior is not '
            'specified in (and currently does not conform to) RFC 7231.',
            DeprecationWarning,
        )
        best_quality = -1
        best_offer = default_match
        for offer in offers:
            if isinstance(offer, (list, tuple)):
                offer, quality = offer
            else:
                quality = 1
            if quality > best_quality:
                best_offer = offer
                best_quality = quality
        return best_offer

    def lookup(
        self, language_tags=None, default_range=None, default_tag=None,
        default=None,
    ):
        """
        Return the language tag that best matches the header, using Lookup.

        When the header is invalid, or there is no ``Accept-Language`` header
        in the request, all language tags are considered acceptable, so it is
        as if the header is '*'. As specified for the Lookup matching scheme in
        :rfc:`RFC 4647, section 3.4 <4647#section-3.4>`, when the header is
        '*', the default value is to be computed and returned. So this method
        will ignore the `language_tags` and `default_range` arguments, and
        proceed to `default_tag`, then `default`.

        :param language_tags: (optional, any type)

                              | This argument is ignored, and is only used as a
                                placeholder so that the method signature
                                corresponds to that of
                                :meth:`AcceptLanguageValidHeader.lookup`.

        :param default_range: (optional, any type)

                              | This argument is ignored, and is only used as a
                                placeholder so that the method signature
                                corresponds to that of
                                :meth:`AcceptLanguageValidHeader.lookup`.

        :param default_tag: (optional, ``None`` or ``str``)

                            | At least one of `default_tag` or `default` must
                              be supplied as an argument to the method, to
                              define the defaulting behaviour.

                            | If this argument is not ``None``, then it is
                              returned.

                            | This parameter corresponds to "return a
                              particular language tag designated for the
                              operation", one of the examples of "defaulting
                              behavior" described in :rfc:`RFC 4647, section
                              3.4.1 <4647#section-3.4.1>`.

        :param default: (optional, ``None`` or any type, including a callable)

                        | At least one of `default_tag` or `default` must be
                          supplied as an argument to the method, to define the
                          defaulting behaviour.

                        | If `default_tag` is ``None``, then Lookup will next
                          examine the `default` argument.

                        | If `default` is a callable, it will be called, and
                          the callable's return value will be returned.

                        | If `default` is not a callable, the value itself will
                          be returned.

                        | This parameter corresponds to the "defaulting
                          behavior" described in :rfc:`RFC 4647, section 3.4.1
                          <4647#section-3.4.1>`

        :return: (``str``, or any type)

                 | the return value from `default_tag` or `default`.
        """
        if default_tag is None and default is None:
            raise TypeError(
                '`default_tag` and `default` arguments cannot both be None.'
            )

        if default_tag is not None:
            return default_tag

        try:
            return default()
        except TypeError:  # default is not a callable
            return default

    def quality(self, offer):
        """
        Return quality value of given offer, or ``None`` if there is no match.

        This is the ``.quality()`` method for when the header is invalid or not
        found in the request, corresponding to
        :meth:`AcceptLanguageValidHeader.quality`.

        .. warning::

           This is currently maintained for backward compatibility, and will be
           deprecated in the future (see the documentation for
           :meth:`AcceptLanguageValidHeader.quality`).

        :param offer: (``str``) language tag offer
        :return: (``float``) ``1.0``.

        When the ``Accept-Language`` header is invalid or not in the request,
        all offers are equally acceptable, so 1.0 is always returned.
        """
        warnings.warn(
            'The behavior of .quality for the AcceptLanguage classes is '
            'currently being maintained for backward compatibility, but the '
            'method will be deprecated in the future, as its behavior is not '
            'specified in (and currently does not conform to) RFC 7231.',
            DeprecationWarning,
        )
        return 1.0


class AcceptLanguageNoHeader(_AcceptLanguageInvalidOrNoHeader):
    """
    Represent when there is no ``Accept-Language`` header in the request.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptLanguageNoHeader.__add__`).
    """

    def __init__(self):
        """
        Create an :class:`AcceptLanguageNoHeader` instance.
        """
        self._header_value = None
        self._parsed = None
        self._parsed_nonzero = None

    @property
    def header_value(self):
        """
        (``str`` or ``None``) The header value.

        As there is no header in the request, this is ``None``.
        """
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        As there is no header in the request, this is ``None``.
        """
        return self._parsed

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str``
        * a ``dict``, with language ranges as keys and qvalues as values
        * a ``tuple`` or ``list``, of language range ``str``\ s or of ``tuple``
          or ``list`` (language range, qvalue) pairs (``str``\ s and pairs can be
          mixed within the ``tuple`` or ``list``)
        * an :class:`AcceptLanguageValidHeader`,
          :class:`AcceptLanguageNoHeader`, or
          :class:`AcceptLanguageInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or an
        :class:`AcceptLanguageValidHeader` instance, a new
        :class:`AcceptLanguageValidHeader` instance with the valid header value
        is returned.

        If `other` is ``None``, an :class:`AcceptLanguageNoHeader` instance, an
        invalid header value, or an :class:`AcceptLanguageInvalidHeader`
        instance, a new :class:`AcceptLanguageNoHeader` instance is returned.
        """
        if isinstance(other, AcceptLanguageValidHeader):
            return AcceptLanguageValidHeader(header_value=other.header_value)

        if isinstance(
            other, (AcceptLanguageNoHeader, AcceptLanguageInvalidHeader)
        ):
            return self.__class__()

        return self._add_instance_and_non_accept_language_type(
            instance=self, other=other,
        )

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptLanguageNoHeader.__add__`.
        """
        return self.__add__(other=other)

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    def __str__(self):
        """Return the ``str`` ``'<no header in request>'``."""
        return '<no header in request>'

    def _add_instance_and_non_accept_language_type(self, instance, other):
        if not other:
            return self.__class__()

        other_header_value = self._python_value_to_header_str(value=other)

        try:
            return AcceptLanguageValidHeader(header_value=other_header_value)
        except ValueError:  # invalid header value
            return self.__class__()


class AcceptLanguageInvalidHeader(_AcceptLanguageInvalidOrNoHeader):
    """
    Represent an invalid ``Accept-Language`` header.

    An invalid header is one that does not conform to
    :rfc:`7231#section-5.3.5`. As specified in the RFC, an empty header is an
    invalid ``Accept-Language`` header.

    :rfc:`7231` does not provide any guidance on what should happen if the
    ``Accept-Language`` header has an invalid value. This implementation
    disregards the header, and treats it as if there is no ``Accept-Language``
    header in the request.

    This object should not be modified. To add to the header, we can use the
    addition operators (``+`` and ``+=``), which return a new object (see the
    docstring for :meth:`AcceptLanguageInvalidHeader.__add__`).
    """

    def __init__(self, header_value):
        """
        Create an :class:`AcceptLanguageInvalidHeader` instance.
        """
        self._header_value = header_value
        self._parsed = None
        self._parsed_nonzero = None

    @property
    def header_value(self):
        """(``str`` or ``None``) The header value."""
        return self._header_value

    @property
    def parsed(self):
        """
        (``list`` or ``None``) Parsed form of the header.

        As the header is invalid and cannot be parsed, this is ``None``.
        """
        return self._parsed

    def __add__(self, other):
        """
        Add to header, creating a new header object.

        `other` can be:

        * ``None``
        * a ``str``
        * a ``dict``, with language ranges as keys and qvalues as values
        * a ``tuple`` or ``list``, of language range ``str``\ s or of ``tuple``
          or ``list`` (language range, qvalue) pairs (``str``\ s and pairs can
          be mixed within the ``tuple`` or ``list``)
        * an :class:`AcceptLanguageValidHeader`,
          :class:`AcceptLanguageNoHeader`, or
          :class:`AcceptLanguageInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``

        If `other` is a valid header value or an
        :class:`AcceptLanguageValidHeader` instance, a new
        :class:`AcceptLanguageValidHeader` instance with the valid header value
        is returned.

        If `other` is ``None``, an :class:`AcceptLanguageNoHeader` instance, an
        invalid header value, or an :class:`AcceptLanguageInvalidHeader`
        instance, a new :class:`AcceptLanguageNoHeader` instance is returned.
        """
        if isinstance(other, AcceptLanguageValidHeader):
            return AcceptLanguageValidHeader(header_value=other.header_value)

        if isinstance(
            other, (AcceptLanguageNoHeader, AcceptLanguageInvalidHeader)
        ):
            return AcceptLanguageNoHeader()

        return self._add_instance_and_non_accept_language_type(
            instance=self, other=other,
        )

    def __radd__(self, other):
        """
        Add to header, creating a new header object.

        See the docstring for :meth:`AcceptLanguageValidHeader.__add__`.
        """
        return self._add_instance_and_non_accept_language_type(
            instance=self, other=other, instance_on_the_right=True,
        )

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)
        # We do not display the header_value, as it is untrusted input. The
        # header_value could always be easily obtained from the .header_value
        # property.

    def __str__(self):
        """Return the ``str`` ``'<invalid header value>'``."""
        return '<invalid header value>'

    def _add_instance_and_non_accept_language_type(
        self, instance, other, instance_on_the_right=False,
    ):
        if not other:
            return AcceptLanguageNoHeader()

        other_header_value = self._python_value_to_header_str(value=other)

        try:
            return AcceptLanguageValidHeader(header_value=other_header_value)
        except ValueError:  # invalid header value
            return AcceptLanguageNoHeader()


def create_accept_language_header(header_value):
    """
    Create an object representing the ``Accept-Language`` header in a request.

    :param header_value: (``str``) header value
    :return: If `header_value` is ``None``, an :class:`AcceptLanguageNoHeader`
             instance.

             | If `header_value` is a valid ``Accept-Language`` header, an
               :class:`AcceptLanguageValidHeader` instance.

             | If `header_value` is an invalid ``Accept-Language`` header, an
               :class:`AcceptLanguageInvalidHeader` instance.
    """
    if header_value is None:
        return AcceptLanguageNoHeader()
    try:
        return AcceptLanguageValidHeader(header_value=header_value)
    except ValueError:
        return AcceptLanguageInvalidHeader(header_value=header_value)


def accept_language_property():
    doc = """
        Property representing the ``Accept-Language`` header.

        (:rfc:`RFC 7231, section 5.3.5 <7231#section-5.3.5>`)

        The header value in the request environ is parsed and a new object
        representing the header is created every time we *get* the value of the
        property. (*set* and *del* change the header value in the request
        environ, and do not involve parsing.)
    """

    ENVIRON_KEY = 'HTTP_ACCEPT_LANGUAGE'

    def fget(request):
        """Get an object representing the header in the request."""
        return create_accept_language_header(
            header_value=request.environ.get(ENVIRON_KEY)
        )

    def fset(request, value):
        """
        Set the corresponding key in the request environ.

        `value` can be:

        * ``None``
        * a ``str``
        * a ``dict``, with language ranges as keys and qvalues as values
        * a ``tuple`` or ``list``, of language range ``str``\ s or of ``tuple``
          or ``list`` (language range, qvalue) pairs (``str``\ s and pairs can
          be mixed within the ``tuple`` or ``list``)
        * an :class:`AcceptLanguageValidHeader`,
          :class:`AcceptLanguageNoHeader`, or
          :class:`AcceptLanguageInvalidHeader` instance
        * object of any other type that returns a value for ``__str__``
        """
        if value is None or isinstance(value, AcceptLanguageNoHeader):
            fdel(request=request)
        else:
            if isinstance(
                value, (AcceptLanguageValidHeader, AcceptLanguageInvalidHeader)
            ):
                header_value = value.header_value
            else:
                header_value = AcceptLanguage._python_value_to_header_str(
                    value=value,
                )
            request.environ[ENVIRON_KEY] = header_value

    def fdel(request):
        """Delete the corresponding key from the request environ."""
        try:
            del request.environ[ENVIRON_KEY]
        except KeyError:
            pass

    return property(fget, fset, fdel, textwrap.dedent(doc))
