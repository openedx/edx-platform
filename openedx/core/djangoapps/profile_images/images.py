"""
Image file manipulation functions related to profile images.
"""
from cStringIO import StringIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _, ugettext_noop as _noop
from PIL import Image

from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_storage


IMAGE_TYPES = {
    'jpeg': {
        'extension': [".jpeg", ".jpg"],
        'mimetypes': ['image/jpeg', 'image/pjpeg'],
        'magic': ["ffd8"]
    },
    'png': {
        'extension': [".png"],
        'mimetypes': ['image/png'],
        'magic': ["89504e470d0a1a0a"]
    },
    'gif': {
        'extension': [".gif"],
        'mimetypes': ['image/gif'],
        'magic': ["474946383961", "474946383761"]
    }
}


def user_friendly_size(size):
    """
    Convert size in bytes to user friendly size.

    Arguments:
        size (int): size in bytes

    Returns:
        user friendly size
    """
    units = [_('bytes'), _('KB'), _('MB')]
    i = 0
    while size >= 1024:
        size /= 1024
        i += 1
    return u'{} {}'.format(size, units[i])


def get_valid_file_types():
    """
    Return comma separated string of valid file types.
    """
    return ', '.join([', '.join(IMAGE_TYPES[ft]['extension']) for ft in IMAGE_TYPES.keys()])


FILE_UPLOAD_TOO_LARGE = _noop(u'The file must be smaller than {image_max_size} in size.'.format(image_max_size=user_friendly_size(settings.PROFILE_IMAGE_MAX_BYTES)))  # pylint: disable=line-too-long
FILE_UPLOAD_TOO_SMALL = _noop(u'The file must be at least {image_min_size} in size.'.format(image_min_size=user_friendly_size(settings.PROFILE_IMAGE_MIN_BYTES)))  # pylint: disable=line-too-long
FILE_UPLOAD_BAD_TYPE = _noop(u'The file must be one of the following types: {valid_file_types}.'.format(valid_file_types=get_valid_file_types()))  # pylint: disable=line-too-long
FILE_UPLOAD_BAD_EXT = _noop(u'The file name extension for this file does not match the file data. The file may be corrupted.')  # pylint: disable=line-too-long
FILE_UPLOAD_BAD_MIMETYPE = _noop(u'The Content-Type header for this file does not match the file data. The file may be corrupted.')  # pylint: disable=line-too-long


class ImageValidationError(Exception):
    """
    Exception to use when the system rejects a user-supplied source image.
    """
    @property
    def user_message(self):
        """
        Translate the developer-facing exception message for API clients.
        """
        # pylint: disable=translation-of-non-string
        return _(self.message)


def validate_uploaded_image(uploaded_file):
    """
    Raises ImageValidationError if the server should refuse to use this
    uploaded file as the source image for a user's profile image.  Otherwise,
    returns nothing.
    """

    # validation code by @pmitros,
    # adapted from https://github.com/pmitros/ProfileXBlock
    # see also: http://en.wikipedia.org/wiki/Magic_number_%28programming%29

    if uploaded_file.size > settings.PROFILE_IMAGE_MAX_BYTES:
        raise ImageValidationError(FILE_UPLOAD_TOO_LARGE)
    elif uploaded_file.size < settings.PROFILE_IMAGE_MIN_BYTES:
        raise ImageValidationError(FILE_UPLOAD_TOO_SMALL)

    # check the file extension looks acceptable
    filename = unicode(uploaded_file.name).lower()
    filetype = [ft for ft in IMAGE_TYPES if any(filename.endswith(ext) for ext in IMAGE_TYPES[ft]['extension'])]
    if not filetype:
        raise ImageValidationError(FILE_UPLOAD_BAD_TYPE)
    filetype = filetype[0]

    # check mimetype matches expected file type
    if uploaded_file.content_type not in IMAGE_TYPES[filetype]['mimetypes']:
        raise ImageValidationError(FILE_UPLOAD_BAD_MIMETYPE)

    # check magic number matches expected file type
    headers = IMAGE_TYPES[filetype]['magic']
    if uploaded_file.read(len(headers[0]) / 2).encode('hex') not in headers:
        raise ImageValidationError(FILE_UPLOAD_BAD_EXT)
    # avoid unexpected errors from subsequent modules expecting the fp to be at 0
    uploaded_file.seek(0)


def _get_scaled_image_file(image_obj, size):
    """
    Given a PIL.Image object, get a resized copy using `size` (square) and
    return a file-like object containing the data saved as a JPEG.

    Note that the file object returned is a django ContentFile which holds
    data in memory (not on disk).
    """
    if image_obj.mode != "RGB":
        image_obj = image_obj.convert("RGB")
    scaled = image_obj.resize((size, size), Image.ANTIALIAS)
    string_io = StringIO()
    scaled.save(string_io, format='JPEG')
    image_file = ContentFile(string_io.getvalue())
    return image_file


def create_profile_images(image_file, profile_image_names):
    """
    Generates a set of image files based on image_file and
    stores them according to the sizes and filenames specified
    in `profile_image_names`.
    """
    image_obj = Image.open(image_file)

    # first center-crop the image if needed (but no scaling yet).
    width, height = image_obj.size
    if width != height:
        side = width if width < height else height
        image_obj = image_obj.crop(((width - side) / 2, (height - side) / 2, (width + side) / 2, (height + side) / 2))

    storage = get_profile_image_storage()
    for size, name in profile_image_names.items():
        scaled_image_file = _get_scaled_image_file(image_obj, size)
        # Store the file.
        try:
            storage.save(name, scaled_image_file)
        finally:
            scaled_image_file.close()


def remove_profile_images(profile_image_names):
    """
    Physically remove the image files specified in `profile_image_names`
    """
    storage = get_profile_image_storage()
    for name in profile_image_names.values():
        storage.delete(name)
