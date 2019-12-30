"""Test that we have defused XML."""


import defusedxml
from lxml import etree

import pytest


@pytest.mark.parametrize("attr", ["XML", "fromstring", "parse"])
def test_etree_is_defused(attr):
    func = getattr(etree, attr)
    assert "defused" in func.__code__.co_filename


def test_entities_arent_resolved():
    # Make sure we have disabled entity resolution.
    xml = '<?xml version="1.0"?><!DOCTYPE mydoc [<!ENTITY hi "Hello">]> <root>&hi;</root>'
    parser = etree.XMLParser()
    with pytest.raises(defusedxml.EntitiesForbidden):
        _ = etree.XML(xml, parser=parser)
