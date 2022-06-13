"""
Safer version of lxml.etree.

It overrides some unsafe functions from lxml.etree with safer versions from defusedxml.
It also includes a safer XMLParser.

For processing xml always prefer this over using lxml.etree directly.

isort:skip_file
"""

# Names are imported into this module so that it can be a stand-in for
# lxml.etree.  The names are not used here, so disable the pylint warning.
# pylint: disable=unused-import, wildcard-import, unused-wildcard-import


from lxml.etree import XMLParser as _XMLParser
from lxml.etree import *  # lint-amnesty, pylint: disable=redefined-builtin
from lxml.etree import _Element, _ElementTree

# This should be imported after lxml.etree so that it overrides the following attributes.
from defusedxml.lxml import XML, fromstring, parse


class XMLParser(_XMLParser):  # pylint: disable=function-redefined
    """
    A safer version of XMLParser which by default disables entity resolution.
    """

    def __init__(self, *args, **kwargs):
        if "resolve_entities" not in kwargs:
            kwargs["resolve_entities"] = False
        super(XMLParser, self).__init__(*args, **kwargs)  # lint-amnesty, pylint: disable=super-with-arguments
