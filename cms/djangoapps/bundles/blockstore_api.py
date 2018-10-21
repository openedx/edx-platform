"""
API Client for Blockstore
"""
from __future__ import absolute_import, print_function, unicode_literals
from collections import namedtuple
from future.moves.urllib.parse import urljoin
from uuid import UUID

from django.conf import settings
import requests


Bundle = namedtuple('Bundle', ['uuid', 'title', 'slug'])
BundleFile = namedtuple('BundleFile', ['bundle_uuid', 'path', 'size', 'public_url', 'data_url'])

def api_url(*path_parts):
    if not settings.BLOCKSTORE_API_URL.endswith('/api/v1/'):
        raise ValueError('BLOCKSTORE_API_URL must end with /api/v1/')
    return settings.BLOCKSTORE_API_URL + '/'.join(path_parts) + '/'


def get_bundle_by_slug(slug):
    """ Retrieve the bundle with the specified slug """

    # TODO: Add a proper API to fetch bundles by slug, and make the slugs unique.
    # Maybe store slugs in a table so even old slugs can still redirect to current ones?
    all_bundles_response = requests.get(api_url('bundles'))
    all_bundles_response.raise_for_status()
    all_bundles = all_bundles_response.json()
    for bundle in all_bundles:
        if bundle['slug'] == slug:
            return Bundle(uuid=UUID(bundle['uuid']), title=bundle['title'], slug=bundle['slug'])
    return None

def get_bundle_file_metadata(bundle_uuid, path):
    assert isinstance(bundle_uuid, UUID)
    # TODO: the following URL needs a weird double // ("".../files//file.xml")
    response = requests.get(api_url('bundles', str(bundle_uuid), 'files/', path))
    response.raise_for_status()
    file_metadata = response.json()
    return BundleFile(
        bundle_uuid=bundle_uuid,
        path=file_metadata['path'],
        size=file_metadata['size'],
        public_url = file_metadata['data'] if file_metadata['public'] else None,
        data_url = file_metadata['data'],
    )

def get_bundle_file_data(bundle_uuid, path):
    """
    Read all the data in the given bundle file and return it as a
    binary string.

    Do not use this for large files!
    """
    metadata = get_bundle_file_metadata(bundle_uuid, path)
    with requests.get(metadata.data_url, stream=True) as r:
        return r.content
