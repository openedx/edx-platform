"""
Helpful methods to use when parsing OLX (XBlock XML)
"""

from collections import namedtuple

from opaque_keys.edx.locator import BundleDefinitionLocator

from openedx.core.djangolib.blockstore_cache import get_bundle_direct_links_with_cache


class BundleFormatException(Exception):
    """
    Raised when certain errors are found when parsing the OLX in a content
    library bundle.
    """


XBlockInclude = namedtuple('XBlockInclude', ['link_id', 'block_type', 'definition_id', 'usage_hint'])


def parse_xblock_include(include_node):
    """
    Given an etree XML node that represents an <xblock-include /> element,
    parse it and return the BundleDefinitionLocator that it points to.
    """
    # An XBlock include looks like:
    # <xblock-include source="link_id" definition="block_type/definition_id" usage="alias" />
    # Where "source" and "usage" are optional.
    if include_node.tag != 'xblock-include':
        # xss-lint: disable=python-wrap-html
        raise BundleFormatException(f"Expected an <xblock-include /> XML node, but got <{include_node.tag}>")
    try:
        definition_path = include_node.attrib['definition']
    except KeyError:
        raise BundleFormatException("<xblock-include> is missing the required definition=\"...\" attribute")  # lint-amnesty, pylint: disable=raise-missing-from
    usage_hint = include_node.attrib.get("usage", None)
    link_id = include_node.attrib.get("source", None)
    # This is pointing to another definition in the same bundle. It looks like:
    # <xblock-include definition="block_type/definition_id" />
    try:
        block_type, definition_id = definition_path.split("/")
    except ValueError:
        raise BundleFormatException(f"Invalid definition attribute: {definition_path}")  # lint-amnesty, pylint: disable=raise-missing-from
    return XBlockInclude(link_id=link_id, block_type=block_type, definition_id=definition_id, usage_hint=usage_hint)


def definition_for_include(parsed_include, parent_definition_key):
    """
    Given a parsed <xblock-include /> element as a XBlockInclude tuple, get the
    definition (OLX file) that it is pointing to.

    Arguments:

    parsed_include: An XBlockInclude tuple

    parent_definition_key: The BundleDefinitionLocator for the XBlock whose OLX
        contained the <xblock-include /> (i.e. the parent).

    Returns: a BundleDefinitionLocator
    """
    if parsed_include.link_id:
        links = get_bundle_direct_links_with_cache(
            parent_definition_key.bundle_uuid,
            # And one of the following will be set:
            bundle_version=parent_definition_key.bundle_version,
            draft_name=parent_definition_key.draft_name,
        )
        try:
            link = links[parsed_include.link_id]
        except KeyError:
            raise BundleFormatException(f"Link not found: {parsed_include.link_id}")  # lint-amnesty, pylint: disable=raise-missing-from
        return BundleDefinitionLocator(
            bundle_uuid=link.bundle_uuid,
            block_type=parsed_include.block_type,
            olx_path=f"{parsed_include.block_type}/{parsed_include.definition_id}/definition.xml",
            bundle_version=link.version,
        )
    else:
        return BundleDefinitionLocator(
            bundle_uuid=parent_definition_key.bundle_uuid,
            block_type=parsed_include.block_type,
            olx_path=f"{parsed_include.block_type}/{parsed_include.definition_id}/definition.xml",
            bundle_version=parent_definition_key.bundle_version,
            draft_name=parent_definition_key.draft_name,
        )
