"""
Super minimal testing for the appsembler.eventtracking.segment module
"""
import pytest
from mock import patch, Mock
from django.test import TestCase

from openedx.core.djangoapps.appsembler.eventtracking.exceptions import (
    EventProcessingError,
)
from openedx.core.djangoapps.appsembler.eventtracking.utils import (
    get_site_config_for_event, get_user_id_from_event
)

from openedx.core.djangoapps.site_configuration.tests.factories import (
    SiteConfigurationFactory,
)

from openedx.core.djangoapps.appsembler.api.tests.factories import (
    OrganizationFactory,
    OrganizationCourseFactory,
)

EVENTTRACKING_MODULE = 'openedx.core.djangoapps.appsembler.eventtracking'


@pytest.mark.django_db
def test_gets_site_config():
    """
    A bit about the event dict.
    It can have the following keys: 'org', 'course_id' but doesn't have to
    have them
    """
    mock_site_config = Mock()

    with patch(EVENTTRACKING_MODULE + '.utils.get_current_site_configuration',
               return_value=mock_site_config):
        site_config = get_site_config_for_event(dict())
    assert site_config == mock_site_config


@pytest.mark.django_db
@pytest.mark.parametrize('context_key', ['org', 'course_id', 'course_key'])
def test_event_has_site_context(context_key):
    """
    A bit about the event dict.
    It can have the following keys: 'org', 'course_id' but doesn't have to
    have them
    """
    site_config = SiteConfigurationFactory()
    org = OrganizationFactory(linked_site=site_config.site)
    org_course = OrganizationCourseFactory(organization=org)

    site_context = dict(
        org=org.short_name,
        course_id=str(org_course.course_id),
        course_key=str(org_course.course_id),
    )

    event_props = {context_key: site_context[context_key]}
    with patch(EVENTTRACKING_MODULE + '.utils.get_current_site_configuration',
               return_value=None):
        site_config = get_site_config_for_event(event_props)
    assert site_config == site_config


@pytest.mark.django_db
def test_event_raises_exception_on_event_props():
    """
    A bit about the event dict.
    It can have the following keys: 'org', 'course_id' but doesn't have to
    have them
    """
    with patch(EVENTTRACKING_MODULE + '.utils.get_current_site_configuration',
               return_value=None):
        with pytest.raises(EventProcessingError):
            get_site_config_for_event(dict())


@pytest.mark.django_db
def test_event_raises_exception_on_no_org_found():
    """
    A bit about the event dict.
    It can have the following keys: 'org', 'course_id' but doesn't have to
    have them
    """
    with patch(EVENTTRACKING_MODULE + '.utils.get_current_site_configuration',
               return_value=None):
        with pytest.raises(EventProcessingError):
            get_site_config_for_event(dict(org='no-org'))


@pytest.mark.django_db
def test_event_raises_exception_on_no_course_id_found(caplog):
    """
    A bit about the event dict.
    It can have the following keys: 'org', 'course_id' but doesn't have to
    have them
    """
    with patch(EVENTTRACKING_MODULE + '.utils.get_current_site_configuration',
               return_value=None):
        with pytest.raises(EventProcessingError):
            get_site_config_for_event(dict(course_id='no-course-id'))
    assert 'get_site_config_for_event: Cannot get site config for event' in caplog.text, 'Should log the exception'


TEST_EVENT_FOR_USER_IDS_ONE = {
    "user_id": None,
    "context": {
        "course_id": "course-v1:org+course+run",
        "path": "/user_api/v1/account/registration/",
        "user_id": 1,  # for example an Instructor
        "org_id": "org"
    },
    "event_type": "edx.course.enrollment.activated",
    "username": "",
    "host": "host.tld",
    "event": {
        "course_id": "course-v1:org+course+run",
        "user_id": 2,
        "context": {
            "user_id": 3
        }
    },
    "referer": "https://host.tld/register"
}

TEST_EVENT_FOR_USER_IDS_TWO = {
    "user_id": 1,
    "context": {
        "course_id": "course-v1:org+course+run",
        "path": "/user_api/v1/account/registration/",
        "user_id": 3,  # for example an Instructor
        "org_id": "org"
    },
    "event_type": "edx.course.enrollment.activated",
    "username": "",
    "host": "host.tld",
    "event": {
        "course_id": "course-v1:org+course+run",
        "user_id": "",  # not sure if this would ever occur, but let's test
    },
    "referer": "https://host.tld/register"
}

TEST_EVENTS_FOR_USER_IDS = [TEST_EVENT_FOR_USER_IDS_ONE, TEST_EVENT_FOR_USER_IDS_TWO]


@pytest.mark.parametrize('event', TEST_EVENTS_FOR_USER_IDS)
def test_get_user_id_from_event(event):
    """
    Test getting user_id from event properties.
    In some cases a user_id may be in context, in others in event.context, or event.context.event.
    """
    # 3 is the id of the deepest valid user_id
    assert get_user_id_from_event(event) == 3
