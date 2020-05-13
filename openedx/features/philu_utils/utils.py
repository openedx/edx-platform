from django.core.validators import ValidationError
from django.utils.translation import ugettext as _


def validate_file_size(file, max_allowed_size):
    """
    Validate maximum allowed file upload size, raise validation error if file size exceeds.
    :param max_allowed_size: maximum allowed file size in bytes
    """
    size = getattr(file, 'size', None)

    if not max_allowed_size:
        raise Exception(
            _('Max allowed size must be specified')
        )

    if size and max_allowed_size < size:
        raise ValidationError(
            _('File size must not exceed {size} MB').format(size=max_allowed_size / 1024 / 1024)
        )


def bytes_to_mb(bytes):
    """Convert size from bytes to MB"""
    return bytes / 1024 / 1024
