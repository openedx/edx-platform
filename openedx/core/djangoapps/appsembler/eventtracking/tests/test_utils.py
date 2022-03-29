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
    get_site_config_for_event,
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
