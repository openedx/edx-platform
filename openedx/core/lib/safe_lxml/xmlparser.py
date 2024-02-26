# Based on the lxml example from defusedxml
#
"""lxml.etree protection"""

from __future__ import print_function, absolute_import

import threading

from lxml import etree as _etree

from defusedxml.common import DTDForbidden, EntitiesForbidden, NotSupportedError

LXML3 = _etree.LXML_VERSION[0] >= 3

__origin__ = "lxml.etree"

tostring = _etree.tostring


class RestrictedElement(_etree.ElementBase):
    """A restricted Element class that filters out instances of some classes
    """

    __slots__ = ()
    blacklist = (_etree._Entity, _etree._ProcessingInstruction, _etree._Comment)  # pylint: disable=protected-access

    def _filter(self, iterator):  # pylint: disable=missing-function-docstring
        blacklist = self.blacklist
        for child in iterator:
            if isinstance(child, blacklist):
                continue
            yield child

    def __iter__(self):
        iterator = super(RestrictedElement, self).__iter__()  # pylint: disable=super-with-arguments
        return self._filter(iterator)

    def iterchildren(self, tag=None, reversed=False):  # pylint: disable=redefined-builtin
        iterator = super(RestrictedElement, self).iterchildren(tag=tag, reversed=reversed)  # pylint: disable=super-with-arguments
        return self._filter(iterator)

    def iter(self, tag=None, *tags):  # pylint: disable=keyword-arg-before-vararg
        iterator = super(RestrictedElement, self).iter(tag=tag, *tags)  # pylint: disable=super-with-arguments
        return self._filter(iterator)

    def iterdescendants(self, tag=None, *tags):  # pylint: disable=keyword-arg-before-vararg
        iterator = super(RestrictedElement, self).iterdescendants(tag=tag, *tags)  # pylint: disable=super-with-arguments
        return self._filter(iterator)

    def itersiblings(self, tag=None, preceding=False):
        iterator = super(RestrictedElement, self).itersiblings(tag=tag, preceding=preceding)  # pylint: disable=super-with-arguments
        return self._filter(iterator)

    def getchildren(self):
        iterator = super(RestrictedElement, self).__iter__()  # pylint: disable=super-with-arguments
        return list(self._filter(iterator))

    def getiterator(self, tag=None):
        iterator = super(RestrictedElement, self).getiterator(tag)  # pylint: disable=super-with-arguments
        return self._filter(iterator)


class GlobalParserTLS(threading.local):
    """Thread local context for custom parser instances
    """

    parser_config = {
        "resolve_entities": False,
    }

    element_class = RestrictedElement

    def createDefaultParser(self):  # pylint: disable=missing-function-docstring
        parser = _etree.XMLParser(**self.parser_config)
        element_class = self.element_class
        if self.element_class is not None:
            lookup = _etree.ElementDefaultClassLookup(element=element_class)
            parser.set_element_class_lookup(lookup)
        return parser

    def setDefaultParser(self, parser):
        self._default_parser = parser  # pylint: disable=attribute-defined-outside-init

    def getDefaultParser(self):  # pylint: disable=missing-function-docstring
        parser = getattr(self, "_default_parser", None)
        if parser is None:
            parser = self.createDefaultParser()
            self.setDefaultParser(parser)
        return parser


_parser_tls = GlobalParserTLS()
getDefaultParser = _parser_tls.getDefaultParser


def check_docinfo(elementtree, forbid_dtd=False, forbid_entities=True):
    """Check docinfo of an element tree for DTD and entity declarations
    The check for entity declarations needs lxml 3 or newer. lxml 2.x does
    not support dtd.iterentities().
    """
    docinfo = elementtree.docinfo
    if docinfo.doctype:
        if forbid_dtd:
            raise DTDForbidden(docinfo.doctype, docinfo.system_url, docinfo.public_id)
        if forbid_entities and not LXML3:
            # lxml < 3 has no iterentities()
            raise NotSupportedError("Unable to check for entity declarations " "in lxml 2.x")  # pylint: disable=implicit-str-concat

    if forbid_entities:
        for dtd in docinfo.internalDTD, docinfo.externalDTD:
            if dtd is None:
                continue
            for entity in dtd.iterentities():
                raise EntitiesForbidden(entity.name, entity.content, None, None, None, None)


def parse(source, parser=None, base_url=None, forbid_dtd=False, forbid_entities=True):  # pylint: disable=missing-function-docstring
    if parser is None:
        parser = getDefaultParser()
    elementtree = _etree.parse(source, parser, base_url=base_url)
    check_docinfo(elementtree, forbid_dtd, forbid_entities)
    return elementtree


def fromstring(text, parser=None, base_url=None, forbid_dtd=False, forbid_entities=True):  # pylint: disable=missing-function-docstring
    if parser is None:
        parser = getDefaultParser()
    rootelement = _etree.fromstring(text, parser, base_url=base_url)
    elementtree = rootelement.getroottree()
    check_docinfo(elementtree, forbid_dtd, forbid_entities)
    return rootelement


XML = fromstring


def iterparse(*args, **kwargs):
    raise NotSupportedError("iterparse not available")
