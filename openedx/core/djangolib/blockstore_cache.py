"""
An API for caching data related to Blockstore bundles

The whole point of this is to make the hard problem of cache invalidation
somewhat less hard.

This cache prefixes all keys with the bundle/draft version number, so that when
any change is made to the bundle/draft, we will look up entries using a new key
and won't find the now-invalid cached data.
"""

from datetime import datetime
from uuid import UUID

from django.conf import settings
from django.core.cache import caches, InvalidCacheBackendError
from pytz import UTC
import requests

from openedx.core.lib import blockstore_api

try:
    # Use a dedicated cache for blockstore, if available:
    cache = caches['blockstore']
except InvalidCacheBackendError:
    cache = caches['default']

# MAX_BLOCKSTORE_CACHE_DELAY:
# The per-bundle/draft caches are automatically invalidated when a newer version
# of the bundle/draft is available, but that automatic check for the current
# version is cached for this many seconds. So in the absence of explicit calls
# to invalidate the cache, data may be out of date by up to this many seconds.
# (Note that we do usually explicitly invalidate this cache during write
# operations though, so this setting mostly affects actions by external systems
# on Blockstore or bugs where we left out the cache invalidation step.)
MAX_BLOCKSTORE_CACHE_DELAY = 60 * 5


class BundleCache:
    """
    Data cache that ties every key-value to a particular version of a blockstore
    bundle/draft, so that if/when the bundle/draft is updated, the cache is
    automatically invalidated.

    The automatic invalidation may take up to MAX_BLOCKSTORE_CACHE_DELAY
    seconds, although the cache can also be manually invalidated for any
    particular bundle versoin/draft by calling .clear()
    """

    def __init__(self, bundle_uuid, draft_name=None):
        """
        Instantiate this wrapper for the bundle with the specified UUID, and
        optionally the specified draft name.
        """
        self.bundle_uuid = bundle_uuid
        self.draft_name = draft_name

    def get(self, key_parts, default=None):
        """
        Get a cached value related to this Blockstore bundle/draft.

        key_parts: an arbitrary list of strings to identify the cached value.
            For example, if caching the XBlock type of an OLX file, one could
            request:
                get(bundle_uuid, ["olx_type", "/path/to/file"])
        default: default value if the key is not set in the cache
        draft_name: read keys related to the specified draft
        """
        assert isinstance(key_parts, (list, tuple))
        full_key = _get_versioned_cache_key(self.bundle_uuid, self.draft_name, key_parts)
        return cache.get(full_key, default)

    def set(self, key_parts, value):
        """
        Set a cached value related to this Blockstore bundle/draft.

        key_parts: an arbitrary list of strings to identify the cached value.
            For example, if caching the XBlock type of an OLX file, one could
            request:
                set(bundle_uuid, ["olx_type", "/path/to/file"], "html")
        value: value to set in the cache
        """
        assert isinstance(key_parts, (list, tuple))
        full_key = _get_versioned_cache_key(self.bundle_uuid, self.draft_name, key_parts)
        return cache.set(full_key, value, timeout=settings.BLOCKSTORE_BUNDLE_CACHE_TIMEOUT)

    def clear(self):
        """
        Clear the cache for the specified bundle or draft.

        This doesn't actually delete keys from the cache, but if the bundle or
        draft has been modified, this will ensure we use the latest version
        number, which will change the key prefix used by this cache, causing the
        old version's keys to become unaddressable and eventually expire.
        """
        # Note: if we switch from memcached to redis at some point, this can be
        # improved because Redis makes it easy to delete all keys with a
        # specific prefix (e.g. a specific bundle UUID), which memcached cannot.
        # With memcached, we just have to leave the invalid keys in the cache
        # (unused) until they expire.
        cache_key = 'bundle_version:{}:{}'.format(self.bundle_uuid, self.draft_name or '')
        cache.delete(cache_key)


def _construct_versioned_cache_key(bundle_uuid, version_num, key_parts, draft_name=None):  # lint-amnesty, pylint: disable=missing-function-docstring
    cache_key = str(bundle_uuid)
    if draft_name:
        cache_key += ":" + draft_name
    cache_key += ":" + str(version_num) + ":" + ":".join(key_parts)
    return cache_key


def _get_versioned_cache_key(bundle_uuid, draft_name, key_parts):
    """
    Generate a cache key string that can be used to store data about the current
    version/draft of the given bundle. The key incorporates the bundle/draft's
    current version number such that if the bundle/draft is updated, a new key
    will be used and the old key will no longer be valid and will expire.

    Pass draft_name=None if you want to use the published version of the bundle.
    """
    assert isinstance(bundle_uuid, UUID)
    version_num = get_bundle_version_number(bundle_uuid, draft_name)
    return _construct_versioned_cache_key(bundle_uuid, version_num, key_parts, draft_name)


def get_bundle_version_number(bundle_uuid, draft_name=None):
    """
    Get the current version number of the specified bundle/draft. If a draft is
    specified, the update timestamp is used in lieu of a version number.
    """
    cache_key = 'bundle_version:{}:{}'.format(bundle_uuid, draft_name or '')
    version = cache.get(cache_key)
    if version is not None:
        return version
    else:
        version = 0  # Default to 0 in case bundle/draft is empty or doesn't exist

    bundle_metadata = blockstore_api.get_bundle(bundle_uuid)
    if draft_name:
        draft_uuid = bundle_metadata.drafts.get(draft_name)  # pylint: disable=no-member
        if draft_uuid:
            draft_metadata = blockstore_api.get_draft(draft_uuid)
            # Convert the 'updated_at' datetime info an integer value with microsecond accuracy.
            updated_at_timestamp = (draft_metadata.updated_at - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds()
            version = int(updated_at_timestamp * 1e6)
            # Cache the draft files using the version.  This saves an API call when the draft is first retrieved.
            draft_files = list(draft_metadata.files.values())
            draft_files_cache_key = _construct_versioned_cache_key(
                bundle_uuid, version, ('bundle_draft_files', ), draft_name)
            cache.set(draft_files_cache_key, draft_files)
    # If we're not using a draft or the draft does not exist [anymore], fall
    # back to the bundle version, if any versions have been published:
    if version == 0 and bundle_metadata.latest_version:
        version = bundle_metadata.latest_version
    cache.set(cache_key, version, timeout=MAX_BLOCKSTORE_CACHE_DELAY)
    return version


def get_bundle_version_files_cached(bundle_uuid, bundle_version):
    """
    Get the files in the specified BundleVersion. Since BundleVersions are
    immutable, this should be cached as aggressively as possible.
    """
    # Use the blockstore django cache directly; this can't use BundleCache because BundleCache only associates data
    # with the most recent bundleversion, not a specified bundleversion
    # This key is '_v2' to avoid reading invalid values cached by a past version of this code with no timeout.
    cache_key = f'bundle_version_files_v2:{bundle_uuid}:{bundle_version}'
    result = cache.get(cache_key)
    if result is None:
        result = blockstore_api.get_bundle_version_files(bundle_uuid, bundle_version)
        # Cache this result. We should be able to cache this forever, since bundle versions are immutable, but currently
        # this result may contain signed S3 URLs which become invalid after 3600 seconds. If Blockstore is improved to
        # return URLs that redirect to the signed S3 URLs, then this can be changed to cache forever.
        cache.set(cache_key, result, timeout=1800)
    return result


def get_bundle_draft_files_cached(bundle_uuid, draft_name):
    """
    Get the files in the specified bundle draft. Cached using BundleCache so we
    get automatic cache invalidation when the draft is updated.
    """
    bundle_cache = BundleCache(bundle_uuid, draft_name)

    cache_key = ('bundle_draft_files', )
    result = bundle_cache.get(cache_key)
    if result is None:
        result = list(blockstore_api.get_bundle_files(bundle_uuid, use_draft=draft_name))
        bundle_cache.set(cache_key, result)
    return result


def get_bundle_files_cached(bundle_uuid, bundle_version=None, draft_name=None):
    """
    Get the list of files in the bundle, optionally with a version and/or draft
    specified.
    """
    if draft_name:
        return get_bundle_draft_files_cached(bundle_uuid, draft_name)
    else:
        if bundle_version is None:
            bundle_version = get_bundle_version_number(bundle_uuid)
        return get_bundle_version_files_cached(bundle_uuid, bundle_version)


def get_bundle_file_metadata_with_cache(bundle_uuid, path, bundle_version=None, draft_name=None):
    """
    Get metadata about a file in a Blockstore Bundle[Version] or Draft, using the
    cached list of files in each bundle if available.
    """
    for file_info in get_bundle_files_cached(bundle_uuid, bundle_version, draft_name):
        if file_info.path == path:
            return file_info
    raise blockstore_api.BundleFileNotFound(f"Could not load {path} from bundle {bundle_uuid}")


def get_bundle_file_data_with_cache(bundle_uuid, path, bundle_version=None, draft_name=None):
    """
    Method to read a file out of a Blockstore Bundle[Version] or Draft, using the
    cached list of files in each bundle if available.
    """
    file_info = get_bundle_file_metadata_with_cache(bundle_uuid, path, bundle_version, draft_name)
    response = requests.get(file_info.url)
    if response.status_code != 200:
        try:
            error_response = response.content.decode('utf-8')[:500]
        except UnicodeDecodeError:
            error_response = '(error details unavailable - response was not a [unicode] string)'
        raise blockstore_api.BundleStorageError(
            "Unexpected error ({}) trying to read {} from bundle {} using URL {}: \n{}".format(
                response.status_code, path, bundle_uuid, file_info.url, error_response,
            )
        )
    return response.content


def get_bundle_version_direct_links_cached(bundle_uuid, bundle_version):
    """
    Get the direct links in the specified BundleVersion. Since BundleVersions
    are immutable, this should be cached as aggressively as possible.
    """
    # Use the blockstore django cache directly; this can't use BundleCache because BundleCache only associates data
    # with the most recent bundleversion, not a specified bundleversion
    cache_key = f'bundle_version_direct_links:{bundle_uuid}:{bundle_version}'
    result = cache.get(cache_key)
    if result is None:
        result = {
            link.name: link.direct
            for link in blockstore_api.get_bundle_version_links(bundle_uuid, bundle_version).values()
        }
        cache.set(cache_key, result, timeout=None)  # Cache forever since bundle versions are immutable
    return result


def get_bundle_draft_direct_links_cached(bundle_uuid, draft_name):
    """
    Get the direct links in the specified bundle draft. Cached using BundleCache
    so we get automatic cache invalidation when the draft is updated.
    """
    bundle_cache = BundleCache(bundle_uuid, draft_name)
    cache_key = ('bundle_draft_direct_links', )
    result = bundle_cache.get(cache_key)
    if result is None:
        links = blockstore_api.get_bundle_links(bundle_uuid, use_draft=draft_name).values()
        result = {link.name: link.direct for link in links}
        bundle_cache.set(cache_key, result)
    return result


def get_bundle_direct_links_with_cache(bundle_uuid, bundle_version=None, draft_name=None):
    """
    Get a dictionary of the direct links of the specified bundle, from cache if
    possible.
    """
    if draft_name:
        links = get_bundle_draft_direct_links_cached(bundle_uuid, draft_name)
    else:
        if bundle_version is None:
            bundle_version = get_bundle_version_number(bundle_uuid)
        links = get_bundle_version_direct_links_cached(bundle_uuid, bundle_version)
    return links
