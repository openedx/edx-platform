"""
Tests for the `get_user_by_username_or_email` helper with `APPSEMBLER_MULTI_TENANT_EMAILS`.
"""

import pytest

from django.contrib.auth import get_user_model
from student.models import get_user_by_username_or_email

from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import (
    create_org_user,
    with_organization_context,
)

User = get_user_model()


@pytest.mark.django_db
def test_get_user_by_username_or_email_single_tenant(settings):
    """
    Ensure `get_user_by_username_or_email` works as upstream intended if APPSEMBLER_MULTI_TENANT_EMAILS is disabled.
    """
    settings.FEATURES = {**settings.FEATURES, 'APPSEMBLER_MULTI_TENANT_EMAILS': False}

    with with_organization_context(site_color='blue1') as blue_org:
        blue_user = create_org_user(blue_org)

    with with_organization_context(site_color='red1') as red_org:
        red_user = create_org_user(red_org)

        # Use red-site context i.e. with `get_current_request`
        assert blue_user == get_user_by_username_or_email(blue_user.username), 'Gets other site user by username'
        assert blue_user == get_user_by_username_or_email(blue_user.email), 'Gets other site user by email'
        assert red_user == get_user_by_username_or_email(red_user.username), 'Gets same site user by username'
        assert red_user == get_user_by_username_or_email(red_user.email), 'Gets same site user by email'

    # Use non-site context i.e. no `get_current_request`
    assert blue_user == get_user_by_username_or_email(blue_user.username), 'works for username without current request'
    assert blue_user == get_user_by_username_or_email(blue_user.email), 'works for email without current request'


@pytest.mark.django_db
def test_get_user_by_username_or_email_multi_tenant(settings):
    """
    Ensure `get_user_by_username_or_email` works with APPSEMBLER_MULTI_TENANT_EMAILS is enabled.
    """
    settings.FEATURES = {**settings.FEATURES, 'APPSEMBLER_MULTI_TENANT_EMAILS': True}

    with with_organization_context(site_color='blue1') as blue_org:
        blue_user = create_org_user(blue_org)

    with with_organization_context(site_color='red1') as red_org:
        red_user = create_org_user(red_org)

        with pytest.raises(User.DoesNotExist):
            # Use red-site context i.e. with `get_current_request`
            # Cannot get other site user by username
            get_user_by_username_or_email(blue_user.username)

        with pytest.raises(User.DoesNotExist):
            # Cannot get other site user by email
            get_user_by_username_or_email(blue_user.email)

        assert red_user == get_user_by_username_or_email(red_user.username), 'Gets same site user by username'
        assert red_user == get_user_by_username_or_email(red_user.email), 'Gets same site user by email'

    # Use non-site context i.e. no `get_current_request`
    with pytest.raises(User.DoesNotExist):
        # should throw exception for username with no current request
        get_user_by_username_or_email(blue_user.username)

    with pytest.raises(User.DoesNotExist):
        # should throw exception for email with no current request
        get_user_by_username_or_email(blue_user.email)
