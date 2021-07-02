"""
All the tests related to admin in webinars app
"""
from datetime import timedelta

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.utils.timezone import now
from mock import Mock, call

from common.djangoapps.student.tests.factories import GroupFactory, UserFactory
from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.lms.applications.admin import adg_admin_site
from openedx.adg.lms.webinars.admin import (
    ActiveWebinarStatusFilter,
    CancelledWebinarAdmin,
    ReadOnlyUserAdmin,
    WebinarAdmin,
    WebinarRegistrationAdmin
)
from openedx.adg.lms.webinars.constants import (
    SEND_UPDATE_EMAILS_FIELD,
    WEBINAR_REGISTRATION_DELETE_PERMISSION_GROUP,
    WEBINAR_STATUS_CANCELLED,
    WEBINAR_STATUS_DELIVERED,
    WEBINAR_STATUS_UPCOMING
)
from openedx.adg.lms.webinars.models import CancelledWebinar, Webinar, WebinarRegistration

from .factories import WebinarFactory, WebinarRegistrationFactory


@pytest.fixture(name='cancelled_webinar_admin')
def cancelled_webinar_admin_fixture():
    site = AdminSite()
    return CancelledWebinarAdmin(CancelledWebinar, site)


@pytest.fixture(name='webinar_admin')
def webinar_admin_fixture():
    site = AdminSite()
    return WebinarAdmin(Webinar, site)


@pytest.fixture(name='readonly_user_admin')
def readonly_user_admin_fixture():
    return ReadOnlyUserAdmin(User, adg_admin_site)


@pytest.fixture(name='webinar_registration_admin')
def webinar_registration_admin_fixture():
    site = AdminSite()
    return WebinarRegistrationAdmin(WebinarRegistration, site)


def test_cancelled_webinar_admin_add_permission():
    """
    Test if CancelledWebinarAdmin does not have add permission
    """
    assert not CancelledWebinarAdmin.has_add_permission('self', Mock())


def test_cancelled_webinar_admin_change_permission():
    """
    Test if CancelledWebinarAdmin does not have change permission
    """
    assert not CancelledWebinarAdmin.has_change_permission('self', Mock())


def test_cancelled_webinar_admin_delete_permission():
    """
    Test if CancelledWebinarAdmin does not have delete permission
    """
    assert not CancelledWebinarAdmin.has_delete_permission('self', Mock())


@pytest.mark.django_db
@pytest.mark.parametrize(
    'webinar_statuses, expected_webinar_count',
    [
        ([Webinar.UPCOMING, Webinar.DELIVERED, Webinar.UPCOMING], 0),
        ([Webinar.CANCELLED, Webinar.DELIVERED, Webinar.UPCOMING], 1),
        ([Webinar.CANCELLED, Webinar.CANCELLED, Webinar.UPCOMING], 2),
        ([Webinar.CANCELLED, Webinar.CANCELLED, Webinar.DELIVERED], 2),
        ([Webinar.CANCELLED, Webinar.CANCELLED, Webinar.CANCELLED], 3)
    ]
)
def test_cancelled_webinar_admin_get_queryset(
    webinar_statuses, expected_webinar_count, cancelled_webinar_admin, request
):
    """
    Test if the queryset for the CancelledWebinarAdmin contains the correct data i.e Cancelled Webinar
    """
    create_test_webinars_as_per_status(webinar_statuses)
    assert cancelled_webinar_admin.get_queryset(request).count() == expected_webinar_count


@pytest.mark.django_db
@pytest.mark.parametrize(
    'webinar_statuses, expected_webinar_count',
    [
        ([Webinar.UPCOMING, Webinar.DELIVERED, Webinar.UPCOMING], 3),
        ([Webinar.CANCELLED, Webinar.DELIVERED, Webinar.UPCOMING], 2),
        ([Webinar.CANCELLED, Webinar.CANCELLED, Webinar.UPCOMING], 1),
        ([Webinar.CANCELLED, Webinar.CANCELLED, Webinar.DELIVERED], 1),
        ([Webinar.CANCELLED, Webinar.CANCELLED, Webinar.CANCELLED], 0)
    ]
)
def test_non_cancelled_webinar_admin_get_queryset(webinar_statuses, expected_webinar_count, webinar_admin, request):
    """
    Test if the queryset for the WebinarAdmin fetches the correct data i.e Non-cancelled webinars
    """
    create_test_webinars_as_per_status(webinar_statuses)
    assert webinar_admin.get_queryset(request).count() == expected_webinar_count


@pytest.mark.django_db
def test_webinar_admin_webinar_status(webinar, delivered_webinar, cancelled_webinar, webinar_admin):
    """
    Test if the WebinarAdmin has correct status
    """
    assert webinar_admin.webinar_status(webinar) == WEBINAR_STATUS_UPCOMING
    assert webinar_admin.webinar_status(delivered_webinar) == WEBINAR_STATUS_DELIVERED
    assert webinar_admin.webinar_status(cancelled_webinar) == WEBINAR_STATUS_CANCELLED


@pytest.mark.django_db
@pytest.mark.parametrize(
    'webinar_statuses, expected_upcoming_count, expected_delivered_count',
    [
        ([Webinar.UPCOMING, Webinar.DELIVERED, Webinar.UPCOMING], 2, 1),
        ([Webinar.DELIVERED, Webinar.DELIVERED, Webinar.UPCOMING], 1, 2),
        ([Webinar.CANCELLED, Webinar.CANCELLED, Webinar.UPCOMING], 1, 0),
        ([Webinar.CANCELLED, Webinar.CANCELLED, Webinar.DELIVERED], 0, 1),
        ([Webinar.CANCELLED, Webinar.CANCELLED, Webinar.CANCELLED], 0, 0)
    ]
)
def test_webinar_admin_custom_status_list_filter(
    webinar_statuses, expected_upcoming_count, expected_delivered_count, webinar_admin, request
):
    """
    Test if the custom list filter `ActiveWebinarStatusFilter` for WebinarAdmin, filters the webinars as expected
    """
    create_test_webinars_as_per_status(webinar_statuses)
    webinar_admin_queryset = webinar_admin.get_queryset(request)

    upcoming_filter = ActiveWebinarStatusFilter(None, {'status': Webinar.UPCOMING}, Webinar, WebinarAdmin)
    assert upcoming_filter.queryset(None, webinar_admin_queryset).count() == expected_upcoming_count

    delivered_filter = ActiveWebinarStatusFilter(None, {'status': Webinar.DELIVERED}, Webinar, WebinarAdmin)
    assert delivered_filter.queryset(None, webinar_admin_queryset).count() == expected_delivered_count


@pytest.mark.django_db
def test_send_update_emails_to_registrants_not_in_webinar_create(webinar_admin_instance, request):
    """
    Test that 'send_update_emails_to_registrants' is not in fields when creating webinar.
    """
    fields = WebinarAdmin.get_fields(webinar_admin_instance, request, None)
    assert 'send_update_emails_to_registrants' not in fields


@pytest.mark.django_db
def test_send_update_emails_to_registrants_in_webinar_update(webinar_admin_instance, request):
    """
    Test that 'send_update_emails_to_registrants' is in fields when modifying webinar.
    """
    fields = WebinarAdmin.get_fields(webinar_admin_instance, request, WebinarFactory())
    assert SEND_UPDATE_EMAILS_FIELD in fields


@pytest.mark.django_db
@pytest.mark.parametrize('update', (True, False))
def test_save_related_send_emails(request, webinar_admin_instance, webinar, mocker, update):
    """
    Test that upon creating/updating webinar, emails for invites/updated invites are sent.
    """
    mock_send_webinar_emails = mocker.patch('openedx.adg.lms.webinars.admin.send_webinar_emails')
    mock_form_class = mocker.patch('openedx.adg.lms.webinars.forms.WebinarForm')

    mock_get_webinar_invitees_emails = mocker.patch('openedx.adg.lms.webinars.admin.get_webinar_invitees_emails')
    mock_get_webinar_invitees_emails.return_value = ['test@email.com']

    request.method = 'POST'
    mock_form_class.instance = webinar

    if update:
        user = UserFactory()
        WebinarRegistrationFactory(user=user, webinar=webinar)
        WebinarAdmin.save_related(webinar_admin_instance, request, mock_form_class, [], update)
        mock_send_webinar_emails.assert_has_calls([
            call(MandrillClient.WEBINAR_UPDATED, webinar, [user.email]),
            call(MandrillClient.WEBINAR_CREATED, webinar, ['test@email.com'])
        ])
    else:
        WebinarAdmin.save_related(webinar_admin_instance, request, mock_form_class, [], update)
        expected_invitee_emails = list({'test@email.com', webinar.presenter.email})
        mock_send_webinar_emails.assert_called_once_with(
            MandrillClient.WEBINAR_CREATED, webinar, expected_invitee_emails
        )


def test_readonly_user_admin_change_permission(readonly_user_admin):
    """
    Test that ReadOnlyUserAdmin does not have any change permissions
    """
    assert not readonly_user_admin.has_change_permission(Mock())


def test_readonly_user_admin_add_permission(readonly_user_admin):
    """
    Test that ReadOnlyUserAdmin does not have any add permissions
    """
    assert not readonly_user_admin.has_add_permission(Mock())


def test_readonly_user_admin_delete_permission(readonly_user_admin):
    """
    Test that ReadOnlyUserAdmin does not have any delete permissions
    """
    assert not readonly_user_admin.has_delete_permission(Mock())


def test_readonly_user_admin_view_permission(readonly_user_admin):
    """
    Test that ReadOnlyUserAdmin has view permission as it is essential for ADG admin user field lookups
    """
    assert readonly_user_admin.has_view_permission(Mock())


def test_readonly_user_admin_get_model_perms(readonly_user_admin):
    """
    Test that ReadOnlyUserAdmin does not appear on the adg admin site index page
    """
    assert readonly_user_admin.get_model_perms(Mock()) == {}


def create_test_webinars_as_per_status(webinar_statues):
    """
    Prepare multiple webinars for test data, one for every status i-e upcoming, delivered and cancelled
    """
    for status in webinar_statues:
        if status == Webinar.UPCOMING:
            WebinarFactory()
        elif status == Webinar.DELIVERED:
            WebinarFactory(end_time=now() - timedelta(hours=1))
        else:
            WebinarFactory(is_cancelled=True)


@pytest.mark.django_db
def test_save_model(webinar_admin_instance, request, webinar):
    """
    Test that the extended `save_model` method stores webinar object prior to updation in `old_webinar` instance
    variable of the model admin and later also persists the updated webinar state in db.
    """
    old_webinar_title = webinar.title

    webinar.title = 'Updated Title'
    webinar_admin_instance.save_model(request, webinar, Mock(), True)

    assert webinar_admin_instance.old_webinar.title == old_webinar_title
    assert Webinar.objects.get(id=webinar.id).title == 'Updated Title'


@pytest.mark.django_db
def test_registration_webinar_admin_delete_permission(request):
    """
    Test that only admins belonging to 'Delete Webinar Registrations' group have
    permission to delete webinar registrations
    """
    request.user = UserFactory()
    assert not WebinarRegistrationAdmin.has_delete_permission('self', request)

    webinar_delete_group = GroupFactory(name=WEBINAR_REGISTRATION_DELETE_PERMISSION_GROUP)
    request.user.groups.add(webinar_delete_group)
    assert WebinarRegistrationAdmin.has_delete_permission('self', request)


@pytest.mark.django_db
def test_get_deleted_objects_webinar_admin(webinar_admin_instance, request, webinar):
    """
    Test that get_deleted_objects for webinar admin returns an empty set of permissions
    """
    request.user = UserFactory()
    # pylint: disable=unused-variable
    deleted_objects, model_count, perms_needed, protected = webinar_admin_instance.get_deleted_objects(
        [webinar], request
    )
    assert perms_needed == set()
