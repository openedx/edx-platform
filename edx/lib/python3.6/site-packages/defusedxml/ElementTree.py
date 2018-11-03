# defusedxml
#
# Copyright (c) 2013 by Christian Heimes <christian@python.org>
# Licensed to PSF under a Contributor Agreement.
# See http://www.python.org/psf/license for licensing details.
"""Defused xml.etree.ElementTree facade
"""
from __future__ import print_function, absolute_import

import sys
from xml.etree.ElementTree import TreeBuilder as _TreeBuilder
from xml.etree.ElementTree import parse as _parse
from xml.etree.ElementTree import tostring

from .common import PY3


if PY3:
    import importlib
else:
    from xml.etree.ElementTree import XMLParser as _XMLParser
    from xml.etree.ElementTree import iterparse as _iterparse
    from xml.etree.ElementTree import ParseError


from .common import (DTDForbidden, EntitiesForbidden,
                     ExternalReferenceForbidden, _generate_etree_functions)

__origin__ = "xml.etree.ElementTree"


def _get_py3_cls():
    """Python 3.3 hides the pure Python code but defusedxml requires it.

    The code is based on test.support.import_fresh_module().
    """
    pymodname = "xml.etree.ElementTree"
    cmodname = "_elementtree"

    pymod = sys.modules.pop(pymodname, None)
    cmod = sys.modules.pop(cmodname, None)

    sys.modules[cmodname] = None
    pure_pymod = importlib.import_module(pymodname)
    if cmod is not None:
        sys.modules[cmodname] = cmod
    else:
        sys.modules.pop(cmodname)
    sys.modules[pymodname] = pymod

    _XMLParser = pure_pymod.XMLParser
    _iterparse = pure_pymod.iterparse
    ParseError = pure_pymod.ParseError

    return _XMLParser, _iterparse, ParseError


if PY3:
    _XMLParser, _iterparse, ParseError = _get_py3_cls()


class DefusedXMLParser(_XMLParser):

    def __init__(self, html=0, target=None, encoding=None,
                 forbid_dtd=False, forbid_entities=True,
                 forbid_external=True):
        # Python 2.x old style class
        _XMLParser.__init__(self, html, target, encoding)
        self.forbid_dtd = forbid_dtd
        self.forbid_entities = forbid_entities
        self.forbid_external = forbid_external
        if PY3:
            parser = self.parser
        else:
            parser = self._parser
        if self.forbid_dtd:
            parser.StartDoctypeDeclHandler = self.defused_start_doctype_decl
        if self.forbid_entities:
            parser.EntityDeclHandler = self.defused_entity_decl
            parser.UnparsedEntityDeclHandler = self.defused_unparsed_entity_decl
        if self.forbid_external:
            parser.ExternalEntityRefHandler = self.defused_external_entity_ref_handler

    def defused_start_doctype_decl(self, name, sysid, pubid,
                                   has_internal_subset):
        raise DTDForbidden(name, sysid, pubid)

    def defused_entity_decl(self, name, is_parameter_entity, value, base,
                            sysid, pubid, notation_name):
        raise EntitiesForbidden(name, value, base, sysid, pubid, notation_name)

    def defused_unparsed_entity_decl(self, name, base, sysid, pubid,
                                     notation_name):
        # expat 1.2
        raise EntitiesForbidden(name, None, base, sysid, pubid, notation_name)

    def defused_external_entity_ref_handler(self, context, base, sysid,
                                            pubid):
        raise ExternalReferenceForbidden(context, base, sysid, pubid)


# aliases
XMLTreeBuilder = XMLParse = DefusedXMLParser

parse, iterparse, fromstring = _generate_etree_functions(DefusedXMLParser,
                                                         _TreeBuilder, _parse,
                                                         _iterparse)
XML = fromstring


__all__ = ['XML', 'XMLParse', 'XMLTreeBuilder', 'fromstring', 'iterparse',
           'parse', 'tostring']
