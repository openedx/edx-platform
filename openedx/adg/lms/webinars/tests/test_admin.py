"""
All the tests related to admin in webinars app
"""
import pytest
from django.contrib.admin.sites import AdminSite
from mock import Mock

from openedx.adg.lms.webinars.admin import ActiveWebinarStatusFilter, CancelledWebinarAdmin, WebinarAdmin
from openedx.adg.lms.webinars.models import CancelledWebinar, Webinar

from .factories import WebinarFactory


@pytest.fixture(name='cancelled_webinar_admin')
def cancelled_webinar_admin_fixture():
    site = AdminSite()
    return CancelledWebinarAdmin(CancelledWebinar, site)


@pytest.fixture(name='webinar_admin')
def webinar_admin_fixture():
    site = AdminSite()
    return WebinarAdmin(Webinar, site)


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
    for webinar_status in webinar_statuses:
        WebinarFactory(status=webinar_status)

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
    for webinar_status in webinar_statuses:
        WebinarFactory(status=webinar_status)

    assert webinar_admin.get_queryset(request).count() == expected_webinar_count


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
    for webinar_status in webinar_statuses:
        WebinarFactory(status=webinar_status)

    webinar_admin_queryset = webinar_admin.get_queryset(request)

    upcoming_filter = ActiveWebinarStatusFilter(None, {'status': Webinar.UPCOMING}, Webinar, WebinarAdmin)
    assert upcoming_filter.queryset(None, webinar_admin_queryset).count() == expected_upcoming_count

    delivered_filter = ActiveWebinarStatusFilter(None, {'status': Webinar.DELIVERED}, Webinar, WebinarAdmin)
    assert delivered_filter.queryset(None, webinar_admin_queryset).count() == expected_delivered_count
