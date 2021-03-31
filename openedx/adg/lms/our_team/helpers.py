"""
Helpers for our team app
"""
from django.core.validators import ValidationError
from django.utils.translation import ugettext as _

from .constants import PROFILE_IMAGE_MAX_SIZE


def validate_profile_image_size(file_):
    """
    Validate maximum allowed file upload size, raise validation error if file size exceeds.

    Arguments:
         file_(object): file that needs to be validated for size

    Returns:
        None
    """
    size = getattr(file_, 'size', None)
    if size and PROFILE_IMAGE_MAX_SIZE < size:
        raise ValidationError(
            _('File size must not exceed {size} MB').format(size=PROFILE_IMAGE_MAX_SIZE / 1024 / 1024)
        )
