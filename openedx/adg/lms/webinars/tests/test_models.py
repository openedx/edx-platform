"""
Tests for all the models in webinars app
"""
from datetime import timedelta
from unittest.mock import Mock

import pytest

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.webinars.constants import BANNER_MAX_SIZE
from openedx.adg.lms.webinars.models import Webinar, WebinarRegistration
from openedx.adg.lms.webinars.tests.factories import WebinarRegistrationFactory


@pytest.mark.django_db
def test_start_date_in_past_for_webinar(webinar):
    """
    Test that exception is thrown when the start_date is in the past for the webinar.
    """
    webinar.start_time -= timedelta(hours=2)
    with pytest.raises(Exception):
        webinar.clean()


@pytest.mark.django_db
def test_end_date_in_past_for_webinar(webinar):
    """
    Test that exception is thrown when the end_date is in the past for the webinar.
    """
    webinar.end_time -= timedelta(hours=3)
    with pytest.raises(Exception):
        webinar.clean()


@pytest.mark.django_db
def test_start_date_greater_than_end_date_for_webinar(webinar):
    """
    Test that exception is thrown when the start_date is greater than end_date for the webinar.
    """
    webinar.start_time = webinar.end_time + timedelta(hours=1)
    with pytest.raises(Exception):
        webinar.clean()


@pytest.mark.django_db
def test_invalid_banner_size_in_webinar(webinar):
    """
    Test that exception is thrown when the banner size is greater than 2MB for the webinar.
    """
    mocked_file = Mock()
    mocked_file.size = BANNER_MAX_SIZE + 1

    webinar.banner = mocked_file
    with pytest.raises(Exception):
        webinar.clean()


@pytest.mark.django_db
def test_valid_banner_size_in_webinar(webinar):
    """
    Test that for valid banner size no exception is thrown.
    """
    mocked_file = Mock()
    mocked_file.size = BANNER_MAX_SIZE

    webinar.banner = mocked_file
    webinar.clean()


@pytest.mark.django_db
def test_delete_single_webinar(mocker, webinar):
    """
    Test deleting a single webinar to check if the Webinar.delete() method works as expected
    """
    mocker.patch('openedx.adg.lms.webinars.models.send_cancellation_emails_for_given_webinars')
    webinar.delete()
    assert webinar.is_cancelled


@pytest.mark.django_db
def test_delete_multiple_webinars(mocker, webinar, delivered_webinar):
    """
    Test deleting a queryset of webinars to check if the WebinarQuerySet.delete() method works as expected
    """
    mocker.patch('openedx.adg.lms.webinars.models.send_cancellation_emails_for_given_webinars')

    Webinar.objects.filter(id__in=[delivered_webinar.id, webinar.id]).delete()

    assert Webinar.objects.filter(id=delivered_webinar.id).first().is_cancelled
    assert Webinar.objects.filter(id=webinar.id).first().is_cancelled


@pytest.mark.django_db
def test_upcoming_webinars(webinar, delivered_webinar):  # pylint: disable=unused-argument
    assert Webinar.objects.upcoming_webinars().count() == 1
    assert Webinar.objects.upcoming_webinars().first() == webinar


@pytest.mark.django_db
def test_delivered_webinars(webinar, delivered_webinar):  # pylint: disable=unused-argument
    assert Webinar.objects.delivered_webinars().count() == 1
    assert Webinar.objects.delivered_webinars().first() == delivered_webinar


@pytest.mark.django_db
def test_remove_team_registrations_and_cancel_reminders(webinar, mocker):
    """
    Test that the function `remove_team_registrations_and_cancel_reminders` removes team registrations and cancels
    reminders of removed members of a webinar
    """
    mock_cancel_all_reminders = mocker.patch('openedx.adg.lms.webinars.models.cancel_all_reminders')

    user_1 = UserFactory()
    user_2 = UserFactory()
    WebinarRegistrationFactory(
        user=user_1, webinar=webinar, is_registered=False, is_team_member_registration=True
    )
    WebinarRegistrationFactory(
        user=user_2, webinar=webinar, is_registered=False, is_team_member_registration=True
    )

    removed_members = [user_1, user_2]
    webinar.remove_team_registrations_and_cancel_reminders(removed_members)

    assert not WebinarRegistration.objects.get(user=user_1).is_team_member_registration
    assert not WebinarRegistration.objects.get(user=user_2).is_team_member_registration

    mock_cancel_all_reminders.assert_called_once()


@pytest.mark.django_db
def test_get_webinar_update_recipients_emails(webinar):
    """
    Tests that the method `get_webinar_update_recipients_emails` correctly returns the update recipients of a webinar
    """
    user_1 = UserFactory()
    user_2 = UserFactory()
    WebinarRegistrationFactory(user=user_1, webinar=webinar)
    WebinarRegistrationFactory(user=user_2, webinar=webinar, is_team_member_registration=True, is_registered=False)

    expected_emails = {user_1.email, user_2.email}
    actual_emails = set(webinar.get_webinar_update_recipients_emails())

    assert expected_emails == actual_emails
