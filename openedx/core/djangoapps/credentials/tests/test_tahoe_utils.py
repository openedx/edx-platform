"""Tests covering Credentials utilities with Tahoe customizations."""

import pytest

from openedx.core.djangoapps.credentials.utils import get_credentials_records_url
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
@pytest.mark.django_db
def test_tahoe_credentials_records_url(settings):
    """
    Credentials is disabled in Tahoe, so get_credentials_records_url() return `None`.
    """
    assert get_credentials_records_url(), 'By default a URL should be returned, otherwise upstream tests will break'

    settings.FEATURES = {'TAHOE_ENABLE_CREDENTIALS': False}
    assert not get_credentials_records_url(), 'In Tahoe production credentials can be disabled'
