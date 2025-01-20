"""
Tests for upstream downstream tracking links.
"""

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from freezegun import freeze_time

from openedx_learning.api.authoring_models import LearningContextLinksStatus, LearningContextLinksStatusChoices

from openedx.core.djangolib.testing.utils import skip_unless_cms
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import BlockFactory, CourseFactory

from ..tasks import create_or_update_upstream_links, create_or_update_xblock_upstream_link


@skip_unless_cms
class TestRecreateUpstreamLinks(ModuleStoreTestCase):
    """
    Test recreate_upstream_links management command.
    """

    ENABLED_SIGNALS = ['course_deleted', 'course_published']

    def setUp(self):
        super().setUp()
        self.now = timezone.now()
        freezer = freeze_time(self.now)
        freezer.start()
        self.addCleanup(freezer.stop)

    def call_command(self, *args, **kwargs):
        """
        call command with pass args.
        """
        out = StringIO()
        kwargs['stdout'] = out
        call_command('recreate_upstream_links', *args, **kwargs)
        return out

    def test_call_with_invalid_args(self):
        """
        Test command with invalid args.
        """
        with self.assertRaisesRegex(CommandError, 'Either --course or --all argument'):
            self.call_command()
        with self.assertRaisesRegex(CommandError, 'Only one of --course or --all argument'):
            self.call_command('--all', '--course', 'some-course')

    @patch(
        'openedx.core.djangoapps.content_libraries.management.commands.recreate_upstream_links.create_or_update_upstream_links'  # pylint: disable=line-too-long
    )
    def test_call_for_single_course(self, mock_task):
        """
        Test command with single course argument
        """
        self.call_command('--course', 'some-course')
        mock_task.delay.assert_called_with('some-course', False, created=self.now)
        # call with --force
        self.call_command('--course', 'some-course', '--force')
        mock_task.delay.assert_called_with('some-course', True, created=self.now)

    @patch(
        'openedx.core.djangoapps.content_libraries.management.commands.recreate_upstream_links.create_or_update_upstream_links'  # pylint: disable=line-too-long
    )
    def test_call_for_multiple_course(self, mock_task):
        """
        Test command with multiple course arguments
        """
        self.call_command('--course', 'some-course', '--course', 'one-more-course')
        mock_task.delay.assert_any_call('some-course', False, created=self.now)
        mock_task.delay.assert_any_call('one-more-course', False, created=self.now)

    @patch(
        'openedx.core.djangoapps.content_libraries.management.commands.recreate_upstream_links.create_or_update_upstream_links'  # pylint: disable=line-too-long
    )
    def test_call_for_all_courses(self, mock_task):
        """
        Test command with multiple course arguments
        """
        course_key_1 = CourseFactory.create(emit_signals=True).id
        course_key_2 = CourseFactory.create(emit_signals=True).id
        self.call_command('--all')
        mock_task.delay.assert_any_call(str(course_key_1), False, created=self.now)
        mock_task.delay.assert_any_call(str(course_key_2), False, created=self.now)


@skip_unless_cms
class TestUpstreamLinksTasks(ModuleStoreTestCase):
    """
    Test tasks related to managing upstream->downstream links.
    """

    ENABLED_SIGNALS = ['course_deleted', 'course_published']

    def setUp(self):
        super().setUp()
        self.now = timezone.now()
        freezer = freeze_time(self.now)
        freezer.start()
        self.addCleanup(freezer.stop)
        self.course = course = CourseFactory.create(emit_signals=True)
        self.course_key = course_key = self.course.id
        self.upstream_1 = "upstream-block-id-1"
        self.upstream_2 = "upstream-block-id-2"
        with self.store.bulk_operations(course_key):
            self.section = BlockFactory.create(parent=course, category="chapter", display_name="Section")
            self.sequence = BlockFactory.create(parent=self.section, category="sequential", display_name="Sequence")
            self.unit = BlockFactory.create(parent=self.sequence, category="vertical", display_name="Unit")
            self.component_1 = BlockFactory.create(
                parent=self.unit,
                category="html",
                display_name="An HTML Block",
                upstream=self.upstream_1,
                upstream_version=1,
            )
            self.component_2 = BlockFactory.create(
                parent=self.unit,
                category="html",
                display_name="Another HTML Block",
                upstream=self.upstream_2,
                upstream_version=1,
            )
            self.component_3 = BlockFactory.create(
                parent=self.unit,
                category="html",
                display_name="Another another HTML Block",
            )

    @patch(
        'openedx.core.djangoapps.content_libraries.api.create_or_update_xblock_upstream_link'
    )
    def test_create_or_update_upstream_links_task(self, mock_api):
        """
        Test task create_or_update_upstream_links for a course
        """
        assert not LearningContextLinksStatus.objects.filter(context_key=str(self.course_key)).exists()
        create_or_update_upstream_links(str(self.course_key), force=False)
        expected_calls = [
            (self.component_1.usage_key, str(self.course_key), self.course.display_name_with_default, self.now),
            (self.component_2.usage_key, str(self.course_key), self.course.display_name_with_default, self.now),
        ]
        assert [(x[0][0].usage_key, x[0][1], x[0][2], x[0][3]) for x in mock_api.call_args_list] == expected_calls
        assert LearningContextLinksStatus.objects.filter(context_key=str(self.course_key)).exists()
        assert LearningContextLinksStatus.objects.filter(
            context_key=str(self.course_key)
        ).first().status == LearningContextLinksStatusChoices.COMPLETED

        mock_api.reset_mock()
        # call again with same course, it should not be processed again
        # as its LearningContextLinksStatusChoices = COMPLETED
        create_or_update_upstream_links(str(self.course_key), force=False)
        mock_api.assert_not_called()
        # again with same course but with force=True, it should be processed now
        create_or_update_upstream_links(str(self.course_key), force=True)
        assert [(x[0][0].usage_key, x[0][1], x[0][2], x[0][3]) for x in mock_api.call_args_list] == expected_calls

    @patch(
        'openedx.core.djangoapps.content_libraries.api.create_or_update_xblock_upstream_link'
    )
    def test_create_or_update_xblock_upstream_link(self, mock_api):
        """
        Test task create_or_update_xblock_upstream_link for a course
        """
        create_or_update_xblock_upstream_link(str(self.component_1.usage_key))
        expected_calls = [
            (self.component_1.usage_key, str(self.course_key), self.course.display_name_with_default),
        ]
        assert [(x[0][0].usage_key, x[0][1], x[0][2]) for x in mock_api.call_args_list] == expected_calls
        mock_api.reset_mock()
        # call for xblock with no upstream
        create_or_update_xblock_upstream_link(str(self.component_3.usage_key))
        mock_api.assert_not_called()

    @patch(
        'openedx.core.djangoapps.content_libraries.api.create_or_update_xblock_upstream_link'
    )
    def test_create_or_update_upstream_links_task_for_invalid_course(self, mock_api):
        """
        Test task create_or_update_upstream_links for an invalid course key.
        """
        course_key = "course-v1:non+existent+course"
        assert not LearningContextLinksStatus.objects.filter(context_key=course_key).exists()
        create_or_update_upstream_links(course_key, force=False)
        mock_api.assert_not_called()
        assert LearningContextLinksStatus.objects.filter(context_key=course_key).exists()
        assert LearningContextLinksStatus.objects.filter(
            context_key=course_key
        ).first().status == LearningContextLinksStatusChoices.FAILED
