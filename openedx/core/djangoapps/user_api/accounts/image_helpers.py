"""
Helper functions for the accounts API.
"""


import hashlib

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage, storages
from django.utils.module_loading import import_string

from common.djangoapps.student.models import UserProfile
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from ..errors import UserNotFound

PROFILE_IMAGE_FILE_EXTENSION = 'jpg'   # All processed profile images are converted to JPEGs

_PROFILE_IMAGE_SIZES = list(settings.PROFILE_IMAGE_SIZES_MAP.values())


def get_profile_image_storage():
    """
    Returns an instance of the configured storage backend for profile images.

    This function prioritizes different settings in the following order to determine
    which storage class to use:

    1. Use 'profile_image' storage from Django's STORAGES if defined (Django 4.2+).
    2. If not available, check the legacy PROFILE_IMAGE_BACKEND setting.
    3. If still undefined, fall back to Django's default_storage.

    Note:
        - Starting in Django 5+, `DEFAULT_FILE_STORAGE` and the `STORAGES` setting
          are mutually exclusive. Only one of them should be used to avoid
          `ImproperlyConfigured` errors.

    Returns:
        An instance of the configured storage backend for handling profile images.

    Raises:
        ImportError: If the specified storage class cannot be imported.
    """
    # Prefer new-style Django 4.2+ STORAGES
    storages_config = getattr(settings, 'STORAGES', {})

    if 'profile_image' in storages_config:
        return storages['profile_image']

    # Legacy fallback: PROFILE_IMAGE_BACKEND
    config = getattr(settings, 'PROFILE_IMAGE_BACKEND', {})
    storage_class_path = config.get('class')
    options = config.get('options', {})

    if not storage_class_path:
        return default_storage

    storage_class = import_string(storage_class_path)
    return storage_class(**options)


def _make_profile_image_name(username):
    """
    Returns the user-specific part of the image filename, based on a hash of
    the username.
    """
    hash_input = settings.PROFILE_IMAGE_HASH_SEED + username
    return hashlib.md5(hash_input.encode('utf-8')).hexdigest()


def _get_profile_image_filename(name, size, file_extension=PROFILE_IMAGE_FILE_EXTENSION):
    """
    Returns the full filename for a profile image, given the name and size.
    """
    return f'{name}_{size}.{file_extension}'


def _get_profile_image_urls(name, storage, file_extension=PROFILE_IMAGE_FILE_EXTENSION, version=None):
    """
    Returns a dict containing the urls for a complete set of profile images,
    keyed by "friendly" name (e.g. "full", "large", "medium", "small").
    """
    def _make_url(size):
        url = storage.url(
            _get_profile_image_filename(name, size, file_extension=file_extension)
        )
        # Return the URL, with the "v" parameter added as its query
        # string with "?v=". If the original URL already includes a
        # query string (such as signed S3 URLs), append to the query
        # string with "&v=" instead.
        separator = '&' if '?' in url else '?'
        return f'{url}{separator}v={version}' if version is not None else url

    return {size_display_name: _make_url(size) for size_display_name, size in settings.PROFILE_IMAGE_SIZES_MAP.items()}


def get_profile_image_names(username):
    """
    Returns a dict containing the filenames for a complete set of profile
    images, keyed by pixel size.
    """
    name = _make_profile_image_name(username)
    return {size: _get_profile_image_filename(name, size) for size in _PROFILE_IMAGE_SIZES}


def get_profile_image_urls_for_user(user, request=None):
    """
    Return a dict {size:url} for each profile image for a given user.
    Notes:
      - this function does not determine whether the set of profile images
    exists, only what the URLs will be if they do exist.  It is assumed that
    callers will use `_get_default_profile_image_urls` instead to provide
    a set of urls that point to placeholder images, when there are no user-
    submitted images.
      - based on the value of django.conf.settings.PROFILE_IMAGE_BACKEND,
    the URL may be relative, and in that case the caller is responsible for
    constructing the full URL if needed.

    Arguments:
        user (django.contrib.auth.User): the user for whom we are getting urls.

    Returns:
        dictionary of {size_display_name: url} for each image.

    """
    try:
        if user.profile.has_profile_image:
            urls = _get_profile_image_urls(
                _make_profile_image_name(user.username),
                get_profile_image_storage(),
                version=user.profile.profile_image_uploaded_at.strftime("%s"),
            )
        else:
            urls = _get_default_profile_image_urls()
    except UserProfile.DoesNotExist:
        # when user does not have profile it raises exception, when exception
        # occur we can simply get default image.
        urls = _get_default_profile_image_urls()

    if request:
        for key, value in urls.items():
            urls[key] = request.build_absolute_uri(value)

    return urls


def _get_default_profile_image_urls():
    """
    Returns a dict {size:url} for a complete set of default profile images,
    used as a placeholder when there are no user-submitted images.

    TODO The result of this function should be memoized, but not in tests.
    """
    return _get_profile_image_urls(
        configuration_helpers.get_value('PROFILE_IMAGE_DEFAULT_FILENAME', settings.PROFILE_IMAGE_DEFAULT_FILENAME),
        staticfiles_storage,
        file_extension=settings.PROFILE_IMAGE_DEFAULT_FILE_EXTENSION,
    )


def set_has_profile_image(username, is_uploaded, upload_dt=None):
    """
    System (not user-facing) API call used to store whether the user has
    uploaded a profile image, and if so, when.  Used by profile_image API.

    Arguments:
        username (django.contrib.auth.User.username): references the user who
            uploaded an image.

        is_uploaded (bool): whether or not the user has an uploaded profile
            image.

        upload_dt (datetime.datetime): If `is_uploaded` is True, this should
            contain the server-side date+time of the upload.  If `is_uploaded`
            is False, the parameter is optional and will be ignored.

    Raises:
        ValueError: is_uploaded was True, but no upload datetime was supplied.
        UserNotFound: no user with username `username` exists.
    """
    if is_uploaded and upload_dt is None:  # lint-amnesty, pylint: disable=no-else-raise
        raise ValueError("No upload datetime was supplied.")
    elif not is_uploaded:
        upload_dt = None
    try:
        profile = UserProfile.objects.get(user__username=username)
    except ObjectDoesNotExist:
        raise UserNotFound()  # lint-amnesty, pylint: disable=raise-missing-from

    profile.profile_image_uploaded_at = upload_dt
    profile.save()
