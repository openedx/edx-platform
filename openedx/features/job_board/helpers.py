"""
Helper methods for Job Board app
"""
from django.core.validators import ValidationError
from django.utils.translation import ugettext as _

from openedx.features.job_board.constants import LOGO_IMAGE_MAX_SIZE


def validate_file_size(file_):
    """
    Validate maximum allowed file upload size, raise validation error if file size exceeds.
    :param file_: file that needs to be validated for size
    """
    size = getattr(file_, 'size', None)
    if size and LOGO_IMAGE_MAX_SIZE < size:
        raise ValidationError(
            _('File size must not exceed {size} MB').format(size=LOGO_IMAGE_MAX_SIZE / 1024 / 1024)
        )
