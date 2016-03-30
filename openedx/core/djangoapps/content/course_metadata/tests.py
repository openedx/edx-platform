"""
Tests for course_metadata app
"""
from mock_django import mock_signal_receiver

from xmodule.modulestore.django import SignalHandler
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from openedx.core.djangoapps.content.course_metadata.signals import listen_for_course_publish
from openedx.core.djangoapps.content.course_metadata.models import CourseAggregatedMetaData
from openedx.core.djangoapps.util.testing import SignalDisconnectTestMixin


class CoursesMetaDataTests(ModuleStoreTestCase):
    """ Test suite for Course Meta Data """

    def setUp(self):
        SignalHandler.course_published.connect(listen_for_course_publish)
        super(CoursesMetaDataTests, self).setUp()

        self.course = CourseFactory.create()
        self.test_data = '<html>Test data</html>'

        self.chapter = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            display_name="Overview",
        )
        self.sub_section = ItemFactory.create(
            parent_location=self.chapter.location,
            category="sequential",
            display_name=u"test subsection",
        )
        self.unit = ItemFactory.create(
            parent_location=self.sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test unit",
        )
        self.content_child1 = ItemFactory.create(
            category="html",
            parent_location=self.unit.location,
            data=self.test_data,
            display_name="Html component"
        )

        self.addCleanup(SignalDisconnectTestMixin.disconnect_course_published_signals)

    def test_course_aggregate_metadata_update_on_course_published(self):
        """
        Test course aggregate metadata update receiver is called on course_published signal
        and CourseAggregatedMetaData is updated
        """
        with mock_signal_receiver(SignalHandler.course_published, wraps=listen_for_course_publish) as receiver:
            self.assertEqual(receiver.call_count, 0)

            # adding new video unit to course should fire the signal
            ItemFactory.create(
                category="video",
                parent_location=self.unit.location,
                data=self.test_data,
                display_name="Video to test aggregates"
            )

            self.assertEqual(receiver.call_count, 1)
            total_assessments = CourseAggregatedMetaData.objects.get(id=self.course.id).total_assessments
            self.assertEqual(total_assessments, 2)

    def test_get_course_aggregate_metadata_by_course_key(self):
        """
        Test course aggregate metadata should compute and return metadata
        when called by get_from_id
        """
        course_metadata = CourseAggregatedMetaData.get_from_id(self.course.id)
        self.assertEqual(course_metadata.total_assessments, 1)
