"""
Helper functions for the accounts API.
"""
import hashlib

from django.conf import settings
from django.core.files.storage import get_storage_class

PROFILE_IMAGE_SIZES_MAP = {
    'full': 500,
    'large': 120,
    'medium': 50,
    'small': 30
}
_PROFILE_IMAGE_SIZES = PROFILE_IMAGE_SIZES_MAP.values()


def get_profile_image_storage():
    """
    Configures and returns a django Storage instance that can be used
    to physically locate, read and write profile images.
    """
    config = settings.PROFILE_IMAGE_BACKEND_CONFIG
    storage_class = get_storage_class(config['storage_class'])
    return storage_class(**config['storage_kwargs'])


def _make_name(username):
    """
    Returns the user-specific part of the image filename, based on a hash of
    the username.
    """
    return hashlib.md5(settings.PROFILE_IMAGE_SECRET_KEY + username).hexdigest()


def _get_filename(name, size):
    """
    Returns the full filename for a profile image, given the name and size.
    """
    return '{name}_{size}.jpg'.format(name=name, size=size)


def _get_urls(name):
    """
    Returns a dict containing the urls for a complete set of profile images,
    keyed by "friendly" name (e.g. "full", "large", "medium", "small").
    """
    storage = get_profile_image_storage()
    return {
        size_display_name: storage.url(_get_filename(name, size))
        for size_display_name, size in PROFILE_IMAGE_SIZES_MAP.items()
    }


def get_profile_image_names(username):
    """
    Returns a dict containing the filenames for a complete set of profile
    images, keyed by pixel size.
    """
    name = _make_name(username)
    return {size: _get_filename(name, size) for size in _PROFILE_IMAGE_SIZES}


def get_profile_image_urls(user):
    """
    Return a dict {size:url} for each profile image for a given user.
    Notes:
      - this function does not determine whether the set of profile images
    exists, only what the URLs will be if they do exist.  It is assumed that
    callers will use `get_default_profile_image_urls` instead to provide
    a set of urls that point to placeholder images, when there are no user-
    submitted images.
      - based on the value of django.conf.settings.PROFILE_IMAGE_BACKEND_CONFIG,
    the URL may be relative, and in that case the caller is responsible for
    constructing the full URL if needed.

    Arguments:
        user (django.contrib.auth.User): the user for whom we are getting urls.

    Returns:
        dictionary of {size_display_name: url} for each image.

    """
    return _get_urls(_make_name(user.username))


def get_default_profile_image_urls():
    """
    Returns a dict {size:url} for a complete set of default profile images,
    used as a placeholder when there are no user-submitted images.

    TODO The result of this function should be memoized, but not in tests.
    """
    return _get_urls(settings.PROFILE_IMAGE_DEFAULT_FILENAME)
