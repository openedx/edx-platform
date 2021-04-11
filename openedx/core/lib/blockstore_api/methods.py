"""
API Client methods for working with Blockstore bundles and drafts
"""

import base64
from urllib.parse import urlencode
from uuid import UUID

import dateutil.parser
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import requests
import six

from .models import (
    Bundle,
    Collection,
    Draft,
    BundleFile,
    DraftFile,
    LinkDetails,
    LinkReference,
    DraftLinkDetails,
)
from .exceptions import (
    NotFound,
    CollectionNotFound,
    BundleNotFound,
    DraftNotFound,
    BundleFileNotFound,
)


def api_url(*path_parts):
    if not settings.BLOCKSTORE_API_URL or not settings.BLOCKSTORE_API_URL.endswith('/api/v1/'):
        raise ImproperlyConfigured('BLOCKSTORE_API_URL must be set and should end with /api/v1/')
    return settings.BLOCKSTORE_API_URL + '/'.join(path_parts)


def api_request(method, url, **kwargs):
    """
    Helper method for making a request to the Blockstore REST API
    """
    if not settings.BLOCKSTORE_API_AUTH_TOKEN:
        raise ImproperlyConfigured("Cannot use Blockstore unless BLOCKSTORE_API_AUTH_TOKEN is set.")
    kwargs.setdefault('headers', {})['Authorization'] = "Token {}".format(settings.BLOCKSTORE_API_AUTH_TOKEN)
    response = requests.request(method, url, **kwargs)
    if response.status_code == 404:
        raise NotFound
    response.raise_for_status()
    if response.status_code == 204:
        return None  # No content
    return response.json()


def _collection_from_response(data):
    """
    Given data about a Collection returned by any blockstore REST API, convert it to
    a Collection instance.
    """
    return Collection(uuid=UUID(data['uuid']), title=data['title'])


def _bundle_from_response(data):
    """
    Given data about a Bundle returned by any blockstore REST API, convert it to
    a Bundle instance.
    """
    return Bundle(
        uuid=UUID(data['uuid']),
        title=data['title'],
        description=data['description'],
        slug=data['slug'],
        # drafts: Convert from a dict of URLs to a dict of UUIDs:
        drafts={draft_name: UUID(url.split('/')[-1]) for (draft_name, url) in data['drafts'].items()},
        # versions field: take the last one and convert it from URL to an int
        # i.e.: [..., 'https://blockstore/api/v1/bundle_versions/bundle_uuid,15'] -> 15
        latest_version=int(data['versions'][-1].split(',')[-1]) if data['versions'] else 0,
    )


def _draft_from_response(data):
    """
    Given data about a Draft returned by any blockstore REST API, convert it to
    a Draft instance.
    """
    return Draft(
        uuid=UUID(data['uuid']),
        bundle_uuid=UUID(data['bundle_uuid']),
        name=data['name'],
        updated_at=dateutil.parser.parse(data['staged_draft']['updated_at']),
        files={
            path: DraftFile(path=path, **file)
            for path, file in data['staged_draft']['files'].items()
        },
        links={
            name: DraftLinkDetails(
                name=name,
                direct=LinkReference(**link["direct"]),
                indirect=[LinkReference(**ind) for ind in link["indirect"]],
                modified=link["modified"],
            )
            for name, link in data['staged_draft']['links'].items()
        }
    )


def get_collection(collection_uuid):
    """
    Retrieve metadata about the specified collection

    Raises CollectionNotFound if the collection does not exist
    """
    assert isinstance(collection_uuid, UUID)
    try:
        data = api_request('get', api_url('collections', str(collection_uuid)))
    except NotFound:
        raise CollectionNotFound("Collection {} does not exist.".format(collection_uuid))
    return _collection_from_response(data)


def create_collection(title):
    """
    Create a new collection.
    """
    result = api_request('post', api_url('collections'), json={"title": title})
    return _collection_from_response(result)


def update_collection(collection_uuid, title):
    """
    Update a collection's title
    """
    assert isinstance(collection_uuid, UUID)
    data = {"title": title}
    result = api_request('patch', api_url('collections', str(collection_uuid)), json=data)
    return _collection_from_response(result)


def delete_collection(collection_uuid):
    """
    Delete a collection
    """
    assert isinstance(collection_uuid, UUID)
    api_request('delete', api_url('collections', str(collection_uuid)))


def get_bundles(uuids=None, text_search=None):
    """
    Get the details of all bundles
    """
    query_params = {}
    if uuids:
        query_params['uuid'] = ','.join(map(str, uuids))
    if text_search:
        query_params['text_search'] = text_search
    version_url = api_url('bundles') + '?' + urlencode(query_params)
    response = api_request('get', version_url)
    # build bundle from response, convert map object to list and return
    return [_bundle_from_response(item) for item in response]


def get_bundle(bundle_uuid):
    """
    Retrieve metadata about the specified bundle

    Raises BundleNotFound if the bundle does not exist
    """
    assert isinstance(bundle_uuid, UUID)
    try:
        data = api_request('get', api_url('bundles', str(bundle_uuid)))
    except NotFound:
        raise BundleNotFound("Bundle {} does not exist.".format(bundle_uuid))
    return _bundle_from_response(data)


def create_bundle(collection_uuid, slug, title="New Bundle", description=""):
    """
    Create a new bundle.

    Note that description is currently required.
    """
    result = api_request('post', api_url('bundles'), json={
        "collection_uuid": str(collection_uuid),
        "slug": slug,
        "title": title,
        "description": description,
    })
    return _bundle_from_response(result)


def update_bundle(bundle_uuid, **fields):
    """
    Update a bundle's title, description, slug, or collection.
    """
    assert isinstance(bundle_uuid, UUID)
    data = {}
    # Most validation will be done by Blockstore, so we don't worry too much about data validation
    for str_field in ("title", "description", "slug"):
        if str_field in fields:
            data[str_field] = fields.pop(str_field)
    if "collection_uuid" in fields:
        data["collection_uuid"] = str(fields.pop("collection_uuid"))
    if fields:
        raise ValueError("Unexpected extra fields passed to update_bundle: {}".format(fields.keys()))
    result = api_request('patch', api_url('bundles', str(bundle_uuid)), json=data)
    return _bundle_from_response(result)


def delete_bundle(bundle_uuid):
    """
    Delete a bundle
    """
    assert isinstance(bundle_uuid, UUID)
    api_request('delete', api_url('bundles', str(bundle_uuid)))


def get_draft(draft_uuid):
    """
    Retrieve metadata about the specified draft.
    If you don't know the draft's UUID, look it up using get_bundle()
    """
    assert isinstance(draft_uuid, UUID)
    try:
        data = api_request('get', api_url('drafts', str(draft_uuid)))
    except NotFound:
        raise DraftNotFound("Draft does not exist: {}".format(draft_uuid))
    return _draft_from_response(data)


def get_or_create_bundle_draft(bundle_uuid, draft_name):
    """
    Retrieve metadata about the specified draft.
    """
    bundle = get_bundle(bundle_uuid)
    try:
        return get_draft(bundle.drafts[draft_name])  # pylint: disable=unsubscriptable-object
    except KeyError:
        # The draft doesn't exist yet, so create it:
        response = api_request('post', api_url('drafts'), json={
            "bundle_uuid": str(bundle_uuid),
            "name": draft_name,
        })
        # The result of creating a draft doesn't include all the fields we want, so retrieve it now:
        return get_draft(UUID(response["uuid"]))


def commit_draft(draft_uuid):
    """
    Commit all of the pending changes in the draft, creating a new version of
    the associated bundle.

    Does not return any value.
    """
    api_request('post', api_url('drafts', str(draft_uuid), 'commit'))


def delete_draft(draft_uuid):
    """
    Delete the specified draft, removing any staged changes/files/deletes.

    Does not return any value.
    """
    api_request('delete', api_url('drafts', str(draft_uuid)))


def get_bundle_version(bundle_uuid, version_number):
    """
    Get the details of the specified bundle version
    """
    if version_number == 0:
        return None
    version_url = api_url('bundle_versions', str(bundle_uuid) + ',' + str(version_number))
    return api_request('get', version_url)


def get_bundle_version_files(bundle_uuid, version_number):
    """
    Get a list of the files in the specified bundle version
    """
    if version_number == 0:
        return []
    version_info = get_bundle_version(bundle_uuid, version_number)
    return [BundleFile(path=path, **file_metadata) for path, file_metadata in version_info["snapshot"]["files"].items()]


def get_bundle_version_links(bundle_uuid, version_number):
    """
    Get a dictionary of the links in the specified bundle version
    """
    if version_number == 0:
        return {}
    version_info = get_bundle_version(bundle_uuid, version_number)
    return {
        name: LinkDetails(
            name=name,
            direct=LinkReference(**link["direct"]),
            indirect=[LinkReference(**ind) for ind in link["indirect"]],
        )
        for name, link in version_info['snapshot']['links'].items()
    }


def get_bundle_files_dict(bundle_uuid, use_draft=None):
    """
    Get a dict of all the files in the specified bundle.

    Returns a dict where the keys are the paths (strings) and the values are
    BundleFile or DraftFile tuples.
    """
    bundle = get_bundle(bundle_uuid)
    if use_draft and use_draft in bundle.drafts:  # pylint: disable=unsupported-membership-test
        draft_uuid = bundle.drafts[use_draft]  # pylint: disable=unsubscriptable-object
        return get_draft(draft_uuid).files
    elif not bundle.latest_version:
        # This bundle has no versions so definitely does not contain any files
        return {}
    else:
        return {file_meta.path: file_meta for file_meta in get_bundle_version_files(bundle_uuid, bundle.latest_version)}


def get_bundle_files(bundle_uuid, use_draft=None):
    """
    Get an iterator over all the files in the specified bundle or draft.
    """
    return get_bundle_files_dict(bundle_uuid, use_draft).values()


def get_bundle_links(bundle_uuid, use_draft=None):
    """
    Get a dict of all the links in the specified bundle.

    Returns a dict where the keys are the link names (strings) and the values
    are LinkDetails or DraftLinkDetails tuples.
    """
    bundle = get_bundle(bundle_uuid)
    if use_draft and use_draft in bundle.drafts:  # pylint: disable=unsupported-membership-test
        draft_uuid = bundle.drafts[use_draft]  # pylint: disable=unsubscriptable-object
        return get_draft(draft_uuid).links
    elif not bundle.latest_version:
        # This bundle has no versions so definitely does not contain any links
        return {}
    else:
        return get_bundle_version_links(bundle_uuid, bundle.latest_version)


def get_bundle_file_metadata(bundle_uuid, path, use_draft=None):
    """
    Get the metadata of the specified file.
    """
    assert isinstance(bundle_uuid, UUID)
    files_dict = get_bundle_files_dict(bundle_uuid, use_draft=use_draft)
    try:
        return files_dict[path]
    except KeyError:
        raise BundleFileNotFound(
            "Bundle {} (draft: {}) does not contain a file {}".format(bundle_uuid, use_draft, path)
        )


def get_bundle_file_data(bundle_uuid, path, use_draft=None):
    """
    Read all the data in the given bundle file and return it as a
    binary string.

    Do not use this for large files!
    """
    metadata = get_bundle_file_metadata(bundle_uuid, path, use_draft)
    with requests.get(metadata.url, stream=True) as r:
        return r.content


def write_draft_file(draft_uuid, path, contents):
    """
    Create or overwrite the file at 'path' in the specified draft with the given
    contents. To delete a file, pass contents=None.

    If you don't know the draft's UUID, look it up using
    get_or_create_bundle_draft()

    Does not return anything.
    """
    api_request('patch', api_url('drafts', str(draft_uuid)), json={
        'files': {
            path: encode_str_for_draft(contents) if contents is not None else None,
        },
    })


def set_draft_link(draft_uuid, link_name, bundle_uuid, version):
    """
    Create or replace the link with the given name in the specified draft so
    that it points to the specified bundle version. To delete a link, pass
    bundle_uuid=None, version=None.

    If you don't know the draft's UUID, look it up using
    get_or_create_bundle_draft()

    Does not return anything.
    """
    api_request('patch', api_url('drafts', str(draft_uuid)), json={
        'links': {
            link_name: {"bundle_uuid": str(bundle_uuid), "version": version} if bundle_uuid is not None else None,
        },
    })


def encode_str_for_draft(input_str):
    """
    Given a string, return UTF-8 representation that is then base64 encoded.
    """
    if isinstance(input_str, six.text_type):
        binary = input_str.encode('utf8')
    else:
        binary = input_str
    return base64.b64encode(binary)


def force_browser_url(blockstore_file_url):
    """
    Ensure that the given URL Blockstore is a URL accessible from the end user's
    browser.
    """
    # Hack: on some devstacks, we must necessarily use different URLs for
    # accessing Blockstore file data from within and outside of docker
    # containers, but Blockstore has no way of knowing which case any particular
    # request is for. So it always returns a URL suitable for use from within
    # the container. Only this edxapp can transform the URL at the last second,
    # knowing that in this case it's going to the user's browser and not being
    # read by edxapp.
    # In production, the same S3 URLs get used for internal and external access
    # so this hack is not necessary.
    return blockstore_file_url.replace('http://edx.devstack.blockstore:', 'http://localhost:')
