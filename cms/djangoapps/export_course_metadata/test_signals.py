"""
Tests for signals.py
"""

from unittest.mock import patch

from edx_toggles.toggles.testutils import override_waffle_flag
from xmodule.modulestore.django import SignalHandler
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory

from .signals import export_course_metadata
from .toggles import EXPORT_COURSE_METADATA_FLAG


@override_waffle_flag(EXPORT_COURSE_METADATA_FLAG, True)
class TestExportCourseMetadata(SharedModuleStoreTestCase):
    """
    Tests for the export_course_metadata function
    """
    ENABLED_SIGNALS = ['course_published']

    def setUp(self):
        super().setUp()
        SignalHandler.course_published.disconnect(export_course_metadata)
        self.course = CourseFactory.create(highlights_enabled_for_messaging=True)
        self.course_key = self.course.id

    def tearDown(self):
        super().tearDown()
        SignalHandler.course_published.disconnect(export_course_metadata)

    def _create_chapter(self, **kwargs):
        BlockFactory.create(
            parent=self.course,
            category='chapter',
            **kwargs
        )

    @patch('cms.djangoapps.export_course_metadata.tasks.course_metadata_export_storage')
    @patch('cms.djangoapps.export_course_metadata.tasks.ContentFile')
    def test_happy_path(self, patched_content, patched_storage):
        """ Ensure we call the storage class with the correct parameters and course metadata """
        all_highlights = [["week1highlight1", "week1highlight2"], ["week1highlight1", "week1highlight2"], [], []]
        with self.store.bulk_operations(self.course_key):
            for week_highlights in all_highlights:
                self._create_chapter(highlights=week_highlights)
        SignalHandler.course_published.connect(export_course_metadata)
        SignalHandler.course_published.send(sender=None, course_key=self.course_key)
        patched_content.assert_called_once_with(
            b'{"highlights": [["week1highlight1", "week1highlight2"], ["week1highlight1", "week1highlight2"], [], []]}'
        )
        patched_storage.save.assert_called_once_with(
            f'course_metadata_export/{self.course_key}.json', patched_content.return_value
        )
