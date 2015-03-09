"""
Image file manipulation functions related to profile images.
"""
from cStringIO import StringIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image

from ..user_api.accounts.api import get_profile_image_storage


class DevMsg(object):
    """
    Holder for pseudo-constants.
    """
    FILE_TOO_LARGE = 'Maximum file size exceeded.'
    FILE_TOO_SMALL = 'Minimum file size not met.'
    FILE_BAD_TYPE = 'Unsupported file type.'
    FILE_BAD_EXT = 'File extension does not match data.'
    FILE_BAD_MIMETYPE = 'Content-Type header does not match data.'


class ImageFileRejected(Exception):
    """
    Exception to use when the system rejects a user-supplied source image.
    """
    pass


def validate_uploaded_image(image_file, content_type):
    """
    Raises ImageFileRejected if the server should refuse to use this
    uploaded file as the source image for a user's profile image.  Otherwise,
    returns nothing.
    """
    # validation code by @pmitros,
    # adapted from https://github.com/pmitros/ProfileXBlock
    # TODO: investigate if PIL has builtin methods for this

    image_types = {
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

    if image_file.size > settings.PROFILE_IMAGE_MAX_BYTES:
        raise ImageFileRejected(DevMsg.FILE_TOO_LARGE)
    elif image_file.size < settings.PROFILE_IMAGE_MIN_BYTES:
        raise ImageFileRejected(DevMsg.FILE_TOO_SMALL)

    # check the file extension looks acceptable
    filename = str(image_file.name).lower()
    filetype = [ft for ft in image_types if any(filename.endswith(ext) for ext in image_types[ft]['extension'])]
    if not filetype:
        raise ImageFileRejected(DevMsg.FILE_BAD_TYPE)
    filetype = filetype[0]

    # check mimetype matches expected file type
    if content_type not in image_types[filetype]['mimetypes']:
        raise ImageFileRejected(DevMsg.FILE_BAD_MIMETYPE)

    # check image file headers match expected file type
    headers = image_types[filetype]['magic']
    if image_file.read(len(headers[0]) / 2).encode('hex') not in headers:
        raise ImageFileRejected(DevMsg.FILE_BAD_EXT)
    # avoid unexpected errors from subsequent modules expecting the fp to be at 0
    image_file.seek(0)


def _get_scaled_image_file(image_obj, size):
    """
    Given a PIL.Image object, get a resized copy using `size` (square) and
    return a file-like object containing the data saved as a JPEG.

    Note that the file object returned is a django ContentFile which holds
    data in memory (not on disk).
    """
    scaled = image_obj.resize((size, size), Image.ANTIALIAS)
    string_io = StringIO()
    scaled.save(string_io, format='JPEG')
    image_file = ContentFile(string_io.getvalue())
    return image_file


def generate_profile_images(image_file, profile_image_names):
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
        # TODO overwrites should be atomic, but FileStorage doesn't support this.
        if storage.exists(name):
            storage.delete(name)
        storage.save(name, scaled_image_file)


def remove_profile_images(profile_image_names):
    """
    Physically remove the image files specified in `profile_image_names`
    """
    storage = get_profile_image_storage()
    for name in profile_image_names.values():
        storage.delete(name)
