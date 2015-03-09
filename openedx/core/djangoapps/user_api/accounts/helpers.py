"""
Helper functions for the accounts API.
"""
import hashlib

from django.conf import settings
from django.core.files.storage import FileSystemStorage, get_storage_class

PROFILE_IMAGE_SIZES_MAP = {
    'full': 500,
    'large': 120,
    'medium': 50,
    'small': 30
}
_PROFILE_IMAGE_SIZES = PROFILE_IMAGE_SIZES_MAP.values()
PROFILE_IMAGE_FORMAT = 'jpg'


def get_profile_image_storage():
    """
    Configures and returns a django Storage instance that can be used
    to physically locate, read and write profile images.
    """
    # Note that, for now, the backend will be FileSystemStorage.  When
    # we eventually support s3 storage, we'll need to pass a parameter
    # to the storage class indicating the s3 bucket which we're using
    # for profile picture uploads.
    storage_class = get_storage_class(settings.PROFILE_IMAGE_BACKEND)
    if storage_class == FileSystemStorage:
        kwargs = {'base_url': (settings.PROFILE_IMAGE_DOMAIN + settings.PROFILE_IMAGE_URL_PATH)}
    return storage_class(**kwargs)


def get_profile_image_name(username):
    """
    Returns the prefix part of the filename used for all profile images.
    """
    return hashlib.md5(settings.PROFILE_IMAGE_SECRET_KEY + username).hexdigest()


def get_profile_image_filename(name, size):
    """
    Returns the full filename for a profile image, given the name prefix and
    size.
    """
    return '{name}_{size}.{format}'.format(name=name, size=size, format=PROFILE_IMAGE_FORMAT)


def get_profile_image_url_for_user(user, size):
    """Return the URL to a user's profile image for a given size.
    Note that based on the value of
    django.conf.settings.PROFILE_IMAGE_DOMAIN, the URL may be relative,
    and in that case the caller is responsible for constructing the full
    URL.

    If the user has not yet uploaded a profile image, return the URL to
    the default edX user profile image.

    Arguments:
        user (django.auth.User): The user for whom we're generating a
        profile image URL.

    Returns:
        string: The URL for the user's profile image.

    Raises:
        ValueError: The caller asked for an unsupported image size.

    TODO refactor to get all the URLs at once, in order to avoid running the hashing
    function 4x as often as necessary.
    """
    if size not in _PROFILE_IMAGE_SIZES:
        raise ValueError('Unsupported profile image size: {size}'.format(size=size))

    if user.profile.has_profile_image:
        name = get_profile_image_name(user.username)
    else:
        name = settings.PROFILE_IMAGE_DEFAULT_FILENAME

    filename = get_profile_image_filename(name, size)
    return settings.get_profile_image_storage().url(filename)


def get_profile_image_names(username):
    """
    Return a dict {size:filename} for each profile image for a given username.
    """
    name = get_profile_image_name(username)
    return {size: get_profile_image_filename(name, size) for size in PROFILE_IMAGE_SIZES.values()}
