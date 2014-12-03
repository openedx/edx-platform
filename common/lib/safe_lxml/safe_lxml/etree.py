"""
Safer version of lxml.etree.

It overrides some unsafe functions from lxml.etree with safer versions from defusedxml.
It also includes a safer XMLParser.

For processing xml always prefer this over using lxml.etree directly.
"""

from lxml.etree import *  # pylint: disable=wildcard-import, unused-wildcard-import
from lxml.etree import XMLParser as _XMLParser

# This should be imported after lxml.etree so that it overrides the following attributes.
from defusedxml.lxml import parse, fromstring, XML


class XMLParser(_XMLParser):  # pylint: disable=function-redefined
    """
    A safer version of XMLParser which by default disables entity resolution.
    """

    def __init__(self, *args, **kwargs):
        if "resolve_entities" not in kwargs:
            kwargs["resolve_entities"] = False
        super(XMLParser, self).__init__(*args, **kwargs)
