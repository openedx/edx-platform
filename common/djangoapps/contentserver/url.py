import re
import uuid

from urlparse import urlparse, urlunparse, parse_qsl
from urllib import urlencode, quote_plus
from opaque_keys.edx.locator import AssetLocator
from opaque_keys.edx.keys import CourseKey, AssetKey
from opaque_keys import InvalidKeyError
from xmodule.assetstore.assetmgr import AssetManager
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.exceptions import NotFoundError
from xmodule.contentstore.content import StaticContent

from . import CONTENTSERVER_VERSION

VERSIONED_ASSETS_PREFIX = '/assets/courseware'
VERSIONED_ASSETS_PATTERN = r'/assets/courseware(/v[\d])?/([a-f0-9]{32})'
ASSET_URL_RE = re.compile(r"""
        /?c4x/
        (?P<org>[^/]+)/
        (?P<course>[^/]+)/
        (?P<category>[^/]+)/
        (?P<name>[^/]+)
    """, re.VERBOSE | re.IGNORECASE)


def is_versioned_asset_path(path):
    """Determines whether the given asset path is versioned."""
    return path.startswith(VERSIONED_ASSETS_PREFIX)


def parse_versioned_asset_path(path):
    """
    Examines an asset path and breaks it apart if it is versioned,
    returning both the asset digest and the unversioned asset path,
    which will normally be an AssetKey.
    """
    asset_digest = None
    asset_path = path
    if is_versioned_asset_path(asset_path):
        result = re.match(VERSIONED_ASSETS_PATTERN, asset_path)
        if result is not None:
            asset_digest = result.groups()[1]
        asset_path = re.sub(VERSIONED_ASSETS_PATTERN, '', asset_path)

    return (asset_digest, asset_path)


def add_version_to_asset_path(path, version):
    """
    Adds a prefix to an asset path indicating the asset's version.
    """

    # Don't version an already-versioned path.
    if is_versioned_asset_path(path):
        return path

    # TODO: this should just use some sort of join-these-url-components-smartly function from stdlib
    return u"{}/v{}/{}{}".format(VERSIONED_ASSETS_PREFIX, CONTENTSERVER_VERSION, version, path)


def get_asset_key_from_path(course_key, path):
    """
    Parses a path, extracting an asset key or creating one.

    Args:
        course_key: key to the course which owns this asset
        path: the path to said content

    Returns:
        AssetKey: the asset key that represents the path
    """

    # Clean up the path, removing any static prefix and any leading slash.
    if path.startswith('/static/'):
        path = path[len('/static/'):]

    path = path.lstrip('/')

    try:
        return AssetKey.from_string(path)
    except InvalidKeyError:
        # If we couldn't parse the path, just let compute_location figure it out.
        # It's most likely a path like /image.png or something.
        return StaticContent.compute_location(course_key, path)


def is_excluded_asset_type(path, excluded_exts):
    """
    Check if this is an allowed file extension to serve.

    Some files aren't served through the CDN in order to avoid same-origin policy/CORS-related issues.
    """
    return any(path.lower().endswith(excluded_ext.lower()) for excluded_ext in excluded_exts)


def get_canonicalized_asset_path(course_key, path, base_url, excluded_exts, encode=True):
    """
    Returns a fully-qualified path to a piece of static content.

    If a static asset CDN is configured, this path will include it.
    Otherwise, the path will simply be relative.

    Args:
        course_key: key to the course which owns this asset
        path: the path to said content

    Returns:
        string: fully-qualified path to asset
    """

    # Break down the input path.
    _, _, relative_path, params, query_string, _ = urlparse(path)

    # Convert our path to an asset key if it isn't one already.
    asset_key = get_asset_key_from_path(course_key, relative_path)

    # Check the status of the asset to see if this can be served via CDN aka publicly.
    serve_from_cdn = False
    content_digest = None
    try:
        content = AssetManager.find(asset_key, as_stream=True)
        serve_from_cdn = not getattr(content, "locked", True)
        content_digest = getattr(content, "content_digest", None)
    except (ItemNotFoundError, NotFoundError):
        # If we can't find the item, just treat it as if it's locked.
        serve_from_cdn = False

    # Do a generic check to see if anything about this asset disqualifies it from being CDN'd.
    is_excluded = False
    if is_excluded_asset_type(relative_path, excluded_exts):
        serve_from_cdn = False
        is_excluded = True

    # Update any query parameter values that have asset paths in them. This is for assets that
    # require their own after-the-fact values, like a Flash file that needs the path of a config
    # file passed to it e.g. /static/visualization.swf?configFile=/static/visualization.xml
    query_params = parse_qsl(query_string)
    updated_query_params = []
    for query_name, query_val in query_params:
        if query_val.startswith('/static/'):
            new_val = get_canonicalized_asset_path(
                course_key, query_val, base_url, excluded_exts, encode=False)
            updated_query_params.append((query_name, new_val))
        else:
            # Make sure we're encoding Unicode strings down to their byte string
            # representation so that `urlencode` can handle it.
            updated_query_params.append((query_name, query_val.encode('utf-8')))

    serialized_asset_key = serialize_asset_key_with_slash(asset_key)
    base_url = base_url if serve_from_cdn else ''
    asset_path = serialized_asset_key

    # If the content has a digest (i.e. md5sum) value specified, create a versioned path to the asset using it.
    if not is_excluded and content_digest:
        asset_path = add_version_to_asset_path(serialized_asset_key, content_digest)

    # Only encode this if told to.  Important so that we don't double encode
    # when working with paths that are in query parameters.
    asset_path = asset_path.encode('utf-8')
    if encode:
        asset_path = quote_plus(asset_path, '/:+@')

    return urlunparse((None, base_url.encode('utf-8'), asset_path, params, urlencode(updated_query_params), None))


def get_base_url_path_for_course_assets(course_key):
    if course_key is None:
        return None

    assert isinstance(course_key, CourseKey)
    placeholder_id = uuid.uuid4().hex
    # create a dummy asset location with a fake but unique name. strip off the name, and return it
    url_path = serialize_asset_key_with_slash(
        course_key.make_asset_key('asset', placeholder_id).for_branch(None)
    )
    return url_path.replace(placeholder_id, '')


def get_location_from_path(path):
    """
    Generate an AssetKey for the given path (old c4x/org/course/asset/name syntax)
    """
    try:
        return AssetKey.from_string(path)
    except InvalidKeyError:
        # TODO - re-address this once LMS-11198 is tackled.
        if path.startswith('/'):
            # try stripping off the leading slash and try again
            return AssetKey.from_string(path[1:])


def serialize_asset_key_with_slash(asset_key):
    """
    Legacy code expects the serialized asset key to start w/ a slash; so, do that in one place
    :param asset_key:
    """
    url = unicode(asset_key)
    if not url.startswith('/'):
        url = '/' + url  # TODO - re-address this once LMS-11198 is tackled.
    return url


def is_c4x_path(path_string):
    """
    Returns a boolean if a path is believed to be a c4x link based on the leading element
    """
    return ASSET_URL_RE.match(path_string) is not None


def get_static_path_from_location(location):
    """
    This utility static method will take a location identifier and create a 'durable' /static/.. URL representation of it.
    This link is 'durable' as it can maintain integrity across cloning of courseware across course-ids, e.g. reruns of
    courses.
    In the LMS/CMS, we have runtime link-rewriting, so at render time, this /static/... format will get translated into
    the actual /c4x/... path which the client needs to reference static content
    """
    if location is not None:
        return u"/static/{name}".format(name=location.name)
    else:
        return None