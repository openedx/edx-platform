"""
Super minimal testing for the appsembler.eventtracking.segment module
"""
from mock import patch, Mock
from django.test import TestCase
import ddt

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


@ddt.ddt
class EventTrackingUtilsTests(TestCase):
    """
    Very basic and very much not exhaustive testing of
    appsembler.eventtracking.utils module
    """
    def setUp(self):
        self.site_config = SiteConfigurationFactory()
        self.org = OrganizationFactory(sites=[self.site_config.site])
        self.org_course = OrganizationCourseFactory(organization=self.org)

        self.site_context = dict(org=self.org.short_name,
                                 course_id=str(self.org_course.course_id))

    def test_gets_site_config(self):
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

    @ddt.data('org', 'course_id')
    def test_event_has_site_context(self, context_key):
        """
        A bit about the event dict.
        It can have the following keys: 'org', 'course_id' but doesn't have to
        have them
        """
        event_props = {context_key: self.site_context[context_key]}
        with patch(EVENTTRACKING_MODULE + '.utils.get_current_site_configuration',
                   return_value=None):
            site_config = get_site_config_for_event(event_props)
        assert site_config == self.site_config

    def test_event_raises_exception_on_event_props(self):
        """
        A bit about the event dict.
        It can have the following keys: 'org', 'course_id' but doesn't have to
        have them
        """
        with patch(EVENTTRACKING_MODULE + '.utils.get_current_site_configuration',
                   return_value=None):
            with self.assertRaises(EventProcessingError):
                get_site_config_for_event(dict())

    def test_event_raises_exception_on_no_org_found(self):
        """
        A bit about the event dict.
        It can have the following keys: 'org', 'course_id' but doesn't have to
        have them
        """
        with patch(EVENTTRACKING_MODULE + '.utils.get_current_site_configuration',
                   return_value=None):
            with self.assertRaises(EventProcessingError):
                get_site_config_for_event(dict(org='no-org'))

    def test_event_raises_exception_on_no_course_id_found(self):
        """
        A bit about the event dict.
        It can have the following keys: 'org', 'course_id' but doesn't have to
        have them
        """
        with patch(EVENTTRACKING_MODULE + '.utils.get_current_site_configuration',
                   return_value=None):
            with self.assertRaises(EventProcessingError):
                get_site_config_for_event(dict(course_id='no-course-id'))
