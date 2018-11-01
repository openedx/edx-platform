"""
APIs for dealing with OLX stored in Blockstore
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
from uuid import UUID

from lxml import etree
import requests

from .bundles import get_bundle_files


log = logging.getLogger(__name__)

# OLX lookup cache:
# Format is _olx_lookup_cache[bundle_uuid][(block_type, url_name)] = BundleFile
# This cache is designed so the cache of any given bundle can be easily invalidated
_olx_lookup_cache = {}


def _cache_bundle_olx(bundle_uuid):
    """
    Scan the specified bundle and load all of the definition keys
    from all OLX files it contains.
    """
    if bundle_uuid in _olx_lookup_cache:
        return  # No need, already done.
    bundle_cache = {}
    for f in get_bundle_files(bundle_uuid):
        if not f.path.endswith('.olx'):
            continue
        # This is an OLX file. Parse it:
        with requests.get(f.data_url, stream=True) as r:
            xml_raw = r.content
        try:
            olx_root_node = etree.fromstring(xml_raw)
        except etree.ParseError as err:
            log.error(
                "Cannot parse OLX in file %s of bundle %s: %s",
                f.path, bundle_uuid, err
            )
            continue
        # Note we do not actually parse the OLX using XBlock code at this point
        # We just look for url_name attributes and assume they are on XBlock nodes
        for node in olx_root_node.iter():
            if 'url_name' in node.attrib:
                new_key = (node.tag, node.get('url_name'))
                if new_key in bundle_cache:
                    log.warning(
                        "Duplicate OLX block key (%s, %s) in bundle %s",
                        new_key[0], new_key[1], bundle_uuid,
                    )
                else:
                    bundle_cache[new_key] = f

    _olx_lookup_cache[bundle_uuid] = bundle_cache


def which_olx_file_contains(definition_key):
    # type: (BundleDefinitionLocator) -> Optional[BundleFile]
    """
    Given a definition_key, return info about the OLX file
    that the block is contained in.

    Returns None if no OLX file is known to contain that definition key.
    """
    _cache_bundle_olx(definition_key.bundle_uuid)
    key = (definition_key.block_type, definition_key.definition_id)
    return _olx_lookup_cache[definition_key.bundle_uuid].get(key)


def list_olx_definitions(bundle_uuid):
    """
    Get a flat list of all the blocks in all the OLX files in the given
    bundle, grouped by the OLX file they're in.

    Return value: a dict whose keys are the OLX file paths and whose
    values are a list of tuples of (block_tupe, definition_id)
    """
    assert isinstance(bundle_uuid, UUID)
    _cache_bundle_olx(bundle_uuid)
    by_path = {}
    for key, file_data in _olx_lookup_cache[bundle_uuid].items():
        path_blocks = by_path.setdefault(file_data.path, [])
        path_blocks.append(key)
    return by_path
