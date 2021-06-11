"""
Tests for all functionality related to UserApplicationAdmin
"""
import pytest

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.applications.admin import UserApplicationAdmin

# pylint: disable=redefined-outer-name


@pytest.fixture
def mock_request(request, mocker):
    """
    Create mock request object with user, this fixture will be passed as a parameter to other pytests or fixtures
    """
    request = mocker.Mock()
    request.user = UserFactory(is_superuser=True, is_staff=True)
    return request


@pytest.mark.django_db
def test_change_user_application_permission_with_super_user(mock_request):
    """
    Test that only superuser is allowed to change user application.
    """
    assert UserApplicationAdmin.has_change_permission('self', mock_request)


@pytest.mark.django_db
def test_change_user_application_permission_restriction_with_only_staff_user(mock_request):
    """
    Test that change user application permission is not available for user who are just staff user and not superuser.
    """
    mock_request.user.is_superuser = False
    assert not UserApplicationAdmin.has_change_permission('self', mock_request)
