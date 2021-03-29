"""
ADG LMS Helpers
"""
from django.core.validators import ValidationError
from django.utils.translation import ugettext as _

from .constants import IMAGE_MAX_SIZE


def get_user_first_name(user):
    """
    Get First name of the user, Checks if first name is available otherwise
    splits full name to get the first name.
    Args:
        user: Auth User instance
    Returns:
        (str) first name of the user

    """
    return user.first_name or user.profile.name.split()[0]


def validate_image_size(file_):
    """
    Validate maximum allowed file upload size, raise validation error if file size exceeds.

    Arguments:
         file_(object): file that needs to be validated for size

    Returns:
        None
    """
    size = getattr(file_, 'size', None)
    if size and IMAGE_MAX_SIZE < size:
        raise ValidationError(_('File size must not exceed {size} KB').format(size=IMAGE_MAX_SIZE / 1024))
