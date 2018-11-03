# flake8: noqa
"""
Shim module between Bleach and html5lib. This makes it easier to upgrade the
html5lib library without having to change a lot of code.
"""

from __future__ import unicode_literals

import re
import string

import six

from bleach._vendor.html5lib import (
    HTMLParser,
    getTreeWalker,
)
from bleach._vendor.html5lib import constants
from bleach._vendor.html5lib.constants import (
    namespaces,
    prefixes,
)
from bleach._vendor.html5lib.constants import _ReparseException as ReparseException
from bleach._vendor.html5lib.filters.base import Filter
from bleach._vendor.html5lib.filters.sanitizer import allowed_protocols
from bleach._vendor.html5lib.filters.sanitizer import Filter as SanitizerFilter
from bleach._vendor.html5lib._inputstream import HTMLInputStream
from bleach._vendor.html5lib.serializer import HTMLSerializer
from bleach._vendor.html5lib._tokenizer import HTMLTokenizer
from bleach._vendor.html5lib._trie import Trie


#: Map of entity name to expanded entity
ENTITIES = constants.entities

#: Trie of html entity string -> character representation
ENTITIES_TRIE = Trie(ENTITIES)

#: Token type constants--these never change
TAG_TOKEN_TYPES = set([
    constants.tokenTypes['StartTag'],
    constants.tokenTypes['EndTag'],
    constants.tokenTypes['EmptyTag']
])
CHARACTERS_TYPE = constants.tokenTypes['Characters']


#: List of HTML tags
HTML_TAGS = [
    tag for namespace, tag in
    (
        list(constants.scopingElements) +
        list(constants.formattingElements) +
        list(constants.specialElements) +
        list(constants.htmlIntegrationPointElements) +
        list(constants.mathmlTextIntegrationPointElements)
    )
]
# Add tags that aren't in html5lib.constants
HTML_TAGS.extend(['abbr'])


class InputStreamWithMemory(object):
    """Wraps an HTMLInputStream to remember characters since last <

    This wraps existing HTMLInputStream classes to keep track of the stream
    since the last < which marked an open tag state.

    """
    def __init__(self, inner_stream):
        self._inner_stream = inner_stream
        self.reset = self._inner_stream.reset
        self.position = self._inner_stream.position
        self._buffer = []

    @property
    def errors(self):
        return self._inner_stream.errors

    def char(self):
        c = self._inner_stream.char()
        # char() can return None if EOF, so ignore that
        if c:
            self._buffer.append(c)
        return c

    def charsUntil(self, characters, opposite=False):
        chars = self._inner_stream.charsUntil(characters, opposite=opposite)
        self._buffer.extend(list(chars))
        return chars

    def unget(self, char):
        if self._buffer:
            self._buffer.pop(-1)
        return self._inner_stream.unget(char)

    def get_tag(self):
        """Returns the stream history since last '<'

        Since the buffer starts at the last '<' as as seen by tagOpenState(),
        we know that everything from that point to when this method is called
        is the "tag" that is being tokenized.

        """
        return six.text_type('').join(self._buffer)

    def start_tag(self):
        """Resets stream history to just '<'

        This gets called by tagOpenState() which marks a '<' that denotes an
        open tag. Any time we see that, we reset the buffer.

        """
        self._buffer = ['<']


class BleachHTMLTokenizer(HTMLTokenizer):
    """Tokenizer that doesn't consume character entities"""
    def __init__(self, consume_entities=False, **kwargs):
        super(BleachHTMLTokenizer, self).__init__(**kwargs)

        self.consume_entities = consume_entities

        # Wrap the stream with one that remembers the history
        self.stream = InputStreamWithMemory(self.stream)

    def __iter__(self):
        last_error_token = None

        for token in super(BleachHTMLTokenizer, self).__iter__():
            if last_error_token is not None:
                if ((last_error_token['data'] == 'expected-closing-tag-but-got-char' and
                     token['data'].lower().strip() not in self.parser.tags)):
                    # We've got either a malformed tag or a pseudo-tag or
                    # something that html5lib wants to turn into a malformed
                    # comment which Bleach clean() will drop so we interfere
                    # with the token stream to handle it more correctly.
                    #
                    # If this is an allowed tag, it's malformed and we just let
                    # the html5lib parser deal with it--we don't enter into this
                    # block.
                    #
                    # If this is not an allowed tag, then we convert it to
                    # characters and it'll get escaped in the sanitizer.
                    token['data'] = self.stream.get_tag()
                    token['type'] = CHARACTERS_TYPE

                    # Yield the adjusted token
                    yield token

                else:
                    yield last_error_token
                    yield token

                last_error_token = None
                continue

            # If the token is a ParseError, we hold on to it so we can get the
            # next token and potentially fix it.
            if token['type'] == constants.tokenTypes['ParseError']:
                last_error_token = token
                continue

            yield token

    def consumeEntity(self, allowedChar=None, fromAttribute=False):
        # If this tokenizer is set to consume entities, then we can let the
        # superclass do its thing.
        if self.consume_entities:
            return super(BleachHTMLTokenizer, self).consumeEntity(allowedChar, fromAttribute)

        # If this tokenizer is set to not consume entities, then we don't want
        # to consume and convert them, so this overrides the html5lib tokenizer's
        # consumeEntity so that it's now a no-op.
        #
        # However, when that gets called, it's consumed an &, so we put that back in
        # the stream.
        if fromAttribute:
            self.currentToken['data'][-1][1] += '&'

        else:
            self.tokenQueue.append({"type": CHARACTERS_TYPE, "data": '&'})

    def tagOpenState(self):
        # This state marks a < that is either a StartTag, EndTag, EmptyTag,
        # or ParseError. In all cases, we want to drop any stream history
        # we've collected so far and we do that by calling start_tag() on
        # the input stream wrapper.
        self.stream.start_tag()
        return super(BleachHTMLTokenizer, self).tagOpenState()

    def emitCurrentToken(self):
        token = self.currentToken

        if ((self.parser.tags is not None and
             token['type'] in TAG_TOKEN_TYPES and
             token['name'].lower() not in self.parser.tags)):
            # If this is a start/end/empty tag for a tag that's not in our
            # allowed list, then it gets stripped or escaped. In both of these
            # cases it gets converted to a Characters token.
            if self.parser.strip:
                # If we're stripping the token, we just throw in an empty
                # string token.
                new_data = ''

            else:
                # If we're escaping the token, we want to escape the exact
                # original string. Since tokenizing also normalizes data
                # and this is a tag-like thing, we've lost some information.
                # So we go back through the stream to get the original
                # string and use that.
                new_data = self.stream.get_tag()

            new_token = {
                'type': CHARACTERS_TYPE,
                'data': new_data
            }

            self.currentToken = new_token
            self.tokenQueue.append(new_token)
            self.state = self.dataState
            return

        super(BleachHTMLTokenizer, self).emitCurrentToken()


class BleachHTMLParser(HTMLParser):
    """Parser that uses BleachHTMLTokenizer"""
    def __init__(self, tags, strip, consume_entities, **kwargs):
        """
        :arg tags: list of allowed tags--everything else is either stripped or
            escaped; if None, then this doesn't look at tags at all
        :arg strip: whether to strip disallowed tags (True) or escape them (False);
            if tags=None, then this doesn't have any effect
        :arg consume_entities: whether to consume entities (default behavior) or
            leave them as is when tokenizing (BleachHTMLTokenizer-added behavior)

        """
        self.tags = [tag.lower() for tag in tags] if tags is not None else None
        self.strip = strip
        self.consume_entities = consume_entities
        super(BleachHTMLParser, self).__init__(**kwargs)

    def _parse(self, stream, innerHTML=False, container='div', scripting=False, **kwargs):
        # Override HTMLParser so we can swap out the tokenizer for our own.
        self.innerHTMLMode = innerHTML
        self.container = container
        self.scripting = scripting
        self.tokenizer = BleachHTMLTokenizer(
            stream=stream,
            consume_entities=self.consume_entities,
            parser=self,
            **kwargs
        )
        self.reset()

        try:
            self.mainLoop()
        except ReparseException:
            self.reset()
            self.mainLoop()


def convert_entity(value):
    """Convert an entity (minus the & and ; part) into what it represents

    This handles numeric, hex, and text entities.

    :arg value: the string (minus the ``&`` and ``;`` part) to convert

    :returns: unicode character or None if it's an ambiguous ampersand that
        doesn't match a character entity

    """
    if value[0] == '#':
        if value[1] in ('x', 'X'):
            return six.unichr(int(value[2:], 16))
        return six.unichr(int(value[1:], 10))

    return ENTITIES.get(value, None)


def convert_entities(text):
    """Converts all found entities in the text

    :arg text: the text to convert entities in

    :returns: unicode text with converted entities

    """
    if '&' not in text:
        return text

    new_text = []
    for part in next_possible_entity(text):
        if not part:
            continue

        if part.startswith('&'):
            entity = match_entity(part)
            if entity is not None:
                converted = convert_entity(entity)

                # If it's not an ambiguous ampersand, then replace with the
                # unicode character. Otherwise, we leave the entity in.
                if converted is not None:
                    new_text.append(converted)
                    remainder = part[len(entity) + 2:]
                    if part:
                        new_text.append(remainder)
                    continue

        new_text.append(part)

    return u''.join(new_text)


def match_entity(stream):
    """Returns first entity in stream or None if no entity exists

    Note: For Bleach purposes, entities must start with a "&" and end with
    a ";". This ignoresambiguous character entities that have no ";" at the
    end.

    :arg stream: the character stream

    :returns: ``None`` or the entity string without "&" or ";"

    """
    # Nix the & at the beginning
    if stream[0] != '&':
        raise ValueError('Stream should begin with "&"')

    stream = stream[1:]

    stream = list(stream)
    possible_entity = ''
    end_characters = '<&=;' + string.whitespace

    # Handle number entities
    if stream and stream[0] == '#':
        possible_entity = '#'
        stream.pop(0)

        if stream and stream[0] in ('x', 'X'):
            allowed = '0123456789abcdefABCDEF'
            possible_entity += stream.pop(0)
        else:
            allowed = '0123456789'

        # FIXME(willkg): Do we want to make sure these are valid number
        # entities? This doesn't do that currently.
        while stream and stream[0] not in end_characters:
            c = stream.pop(0)
            if c not in allowed:
                break
            possible_entity += c

        if possible_entity and stream and stream[0] == ';':
            return possible_entity
        return None

    # Handle character entities
    while stream and stream[0] not in end_characters:
        c = stream.pop(0)
        if not ENTITIES_TRIE.has_keys_with_prefix(possible_entity):
            break
        possible_entity += c

    if possible_entity and stream and stream[0] == ';':
        return possible_entity

    return None


AMP_SPLIT_RE = re.compile('(&)')


def next_possible_entity(text):
    """Takes a text and generates a list of possible entities

    :arg text: the text to look at

    :returns: generator where each part (except the first) starts with an
        "&"

    """
    for i, part in enumerate(AMP_SPLIT_RE.split(text)):
        if i == 0:
            yield part
        elif i % 2 == 0:
            yield '&' + part


class BleachHTMLSerializer(HTMLSerializer):
    """HTMLSerializer that undoes & -> &amp; in attributes"""
    def escape_base_amp(self, stoken):
        """Escapes just bare & in HTML attribute values"""
        # First, undo escaping of &. We need to do this because html5lib's
        # HTMLSerializer expected the tokenizer to consume all the character
        # entities and convert them to their respective characters, but the
        # BleachHTMLTokenizer doesn't do that. For example, this fixes
        # &amp;entity; back to &entity; .
        stoken = stoken.replace('&amp;', '&')

        # However, we do want all bare & that are not marking character
        # entities to be changed to &amp;, so let's do that carefully here.
        for part in next_possible_entity(stoken):
            if not part:
                continue

            if part.startswith('&'):
                entity = match_entity(part)
                # Only leave entities in that are not ambiguous. If they're
                # ambiguous, then we escape the ampersand.
                if entity is not None and convert_entity(entity) is not None:
                    yield '&' + entity + ';'

                    # Length of the entity plus 2--one for & at the beginning
                    # and and one for ; at the end
                    part = part[len(entity) + 2:]
                    if part:
                        yield part
                    continue

            yield part.replace('&', '&amp;')

    def serialize(self, treewalker, encoding=None):
        """Wrap HTMLSerializer.serialize and conver & to &amp; in attribute values

        Note that this converts & to &amp; in attribute values where the & isn't
        already part of an unambiguous character entity.

        """
        in_tag = False
        after_equals = False

        for stoken in super(BleachHTMLSerializer, self).serialize(treewalker, encoding):
            if in_tag:
                if stoken == '>':
                    in_tag = False

                elif after_equals:
                    if stoken != '"':
                        for part in self.escape_base_amp(stoken):
                            yield part

                        after_equals = False
                        continue

                elif stoken == '=':
                    after_equals = True

                yield stoken
            else:
                if stoken.startswith('<'):
                    in_tag = True
                yield stoken
