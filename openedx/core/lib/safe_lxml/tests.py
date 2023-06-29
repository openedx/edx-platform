"""
Test that we have defused XML.

For these tests, the defusing will happen in one or more of the `conftest.py`
files that runs at pytest startup calls `defuse_xml_libs()`.

In production, the defusing happens when the LMS or Studio `wsgi.py` files
call `defuse_xml_libs()`.
"""


from lxml import etree
from xml.etree.ElementTree import ParseError

import pytest


def test_entities_arent_resolved():
    # Make sure we have disabled entity resolution.
    xml = '<?xml version="1.0"?><!DOCTYPE mydoc [<!ENTITY hi "Hello">]> <root>&hi;</root>'
    parser = etree.XMLParser()
    with pytest.raises(ParseError):
        _ = etree.XML(xml, parser=parser)
