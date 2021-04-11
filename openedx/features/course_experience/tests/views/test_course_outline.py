"""
Tests for the Course Outline view and supporting views.
"""


import datetime
import json
import re

import ddt
import six
from completion import waffle
from completion.models import BlockCompletion
from completion.test_utils import CompletionWaffleTestMixin
from django.contrib.sites.models import Site
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from milestones.tests.utils import MilestonesTestCaseMixin
from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey, UsageKey
from pyquery import PyQuery as pq
from pytz import UTC
from six import text_type
from waffle.models import Switch
from waffle.testutils import override_switch

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.course_api.blocks.transformers.milestones import MilestonesAndSpecialExamsTransformer
from lms.djangoapps.gating import api as lms_gating_api
from lms.djangoapps.courseware.tests.factories import StaffFactory
from lms.djangoapps.courseware.tests.helpers import MasqueradeMixin
from lms.djangoapps.experiments.testutils import override_experiment_waffle_flag
from lms.urls import RESET_COURSE_DEADLINES_NAME
from openedx.core.djangoapps.course_date_signals.models import SelfPacedRelativeDatesConfig
from openedx.core.djangoapps.schedules.models import Schedule
from openedx.core.djangoapps.schedules.tests.factories import ScheduleFactory
from openedx.core.lib.gating import api as gating_api
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_experience import RELATIVE_DATES_FLAG
from openedx.features.course_experience.views.course_outline import (
    DEFAULT_COMPLETION_TRACKING_START,
    CourseOutlineFragmentView
)
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ...utils import get_course_outline_block_tree
from .test_course_home import course_home_url

TEST_PASSWORD = 'test'
GATING_NAMESPACE_QUALIFIER = '.gating'


@ddt.ddt
class TestCourseOutlinePage(SharedModuleStoreTestCase, MasqueradeMixin):
    """
    Test the course outline view.
    """

    ENABLED_SIGNALS = ['course_published']

    @classmethod
    def setUpClass(cls):
        """
        Set up an array of various courses to be tested.
        """
        SelfPacedRelativeDatesConfig.objects.create(enabled=True)

        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super(TestCourseOutlinePage, cls).setUpClassAndTestData():
            cls.courses = []
            course = CourseFactory.create(self_paced=True)
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                sequential = ItemFactory.create(category='sequential', parent_location=chapter.location, graded=True, format="Homework")
                vertical = ItemFactory.create(category='vertical', parent_location=sequential.location)
                problem = ItemFactory.create(category='problem', parent_location=vertical.location)
            course.children = [chapter]
            chapter.children = [sequential]
            sequential.children = [vertical]
            vertical.children = [problem]
            cls.courses.append(course)

            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
                sequential2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
                vertical = ItemFactory.create(
                    category='vertical',
                    parent_location=sequential.location,
                    display_name="Vertical 1"
                )
                vertical2 = ItemFactory.create(
                    category='vertical',
                    parent_location=sequential2.location,
                    display_name="Vertical 2"
                )
            course.children = [chapter]
            chapter.children = [sequential, sequential2]
            sequential.children = [vertical]
            sequential2.children = [vertical2]
            cls.courses.append(course)

            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                sequential = ItemFactory.create(
                    category='sequential',
                    parent_location=chapter.location,
                    due=datetime.datetime.now(),
                    graded=True,
                    format='Homework',
                )
                vertical = ItemFactory.create(category='vertical', parent_location=sequential.location)
            course.children = [chapter]
            chapter.children = [sequential]
            sequential.children = [vertical]
            cls.courses.append(course)

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.user = UserFactory(password=TEST_PASSWORD)
        for course in cls.courses:
            enrollment = CourseEnrollment.enroll(cls.user, course.id)
            ScheduleFactory.create(
                start_date=timezone.now() - datetime.timedelta(days=1),
                enrollment=enrollment
            )

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseOutlinePage, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    @override_experiment_waffle_flag(RELATIVE_DATES_FLAG, active=True)
    def test_outline_details(self):
        for course in self.courses:

            url = course_home_url(course)

            request_factory = RequestFactory()
            request = request_factory.get(url)
            request.user = self.user

            course_block_tree = get_course_outline_block_tree(
                request, str(course.id), self.user
            )

            response = self.client.get(url)
            self.assertTrue(course.children)
            for chapter in course_block_tree['children']:
                self.assertContains(response, chapter['display_name'])
                self.assertTrue(chapter['children'])
                for sequential in chapter['children']:
                    self.assertContains(response, sequential['display_name'])
                    if sequential['graded']:
                        print(sequential)
                        self.assertContains(response, sequential['due'].strftime(u'%Y-%m-%d %H:%M:%S'))
                        self.assertContains(response, sequential['format'])
                    self.assertTrue(sequential['children'])

    def test_num_graded_problems(self):
        course = CourseFactory.create()
        with self.store.bulk_operations(course.id):
            chapter = ItemFactory.create(category='chapter', parent_location=course.location)
            sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
            problem = ItemFactory.create(category='problem', parent_location=sequential.location)
            sequential2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
            problem2 = ItemFactory.create(category='problem', graded=True, has_score=True,
                                          parent_location=sequential2.location)
            sequential3 = ItemFactory.create(category='sequential', parent_location=chapter.location)
            problem3_1 = ItemFactory.create(category='problem', graded=True, has_score=True,
                                            parent_location=sequential3.location)
            problem3_2 = ItemFactory.create(category='problem', graded=True, has_score=True,
                                            parent_location=sequential3.location)
        course.children = [chapter]
        chapter.children = [sequential, sequential2, sequential3]
        sequential.children = [problem]
        sequential2.children = [problem2]
        sequential3.children = [problem3_1, problem3_2]
        CourseEnrollment.enroll(self.user, course.id)

        url = course_home_url(course)
        response = self.client.get(url)
        content = response.content.decode('utf8')
        self.assertRegex(content, sequential.display_name + r'\s*</h4>')
        self.assertRegex(content, sequential2.display_name + r'\s*\(1 Question\)\s*</h4>')
        self.assertRegex(content, sequential3.display_name + r'\s*\(2 Questions\)\s*</h4>')

    @override_experiment_waffle_flag(RELATIVE_DATES_FLAG, active=True)
    @ddt.data(
        ([CourseMode.AUDIT, CourseMode.VERIFIED], CourseMode.AUDIT, False, True),
        ([CourseMode.AUDIT, CourseMode.VERIFIED], CourseMode.VERIFIED, False, True),
        ([CourseMode.AUDIT, CourseMode.VERIFIED, CourseMode.MASTERS], CourseMode.MASTERS, False, True),
        ([CourseMode.PROFESSIONAL], CourseMode.PROFESSIONAL, False, True),
        ([CourseMode.AUDIT, CourseMode.VERIFIED], CourseMode.VERIFIED, True, False),
    )
    @ddt.unpack
    def test_reset_course_deadlines_banner_shows_for_self_paced_course(
        self,
        course_modes,
        enrollment_mode,
        is_course_staff,
        should_display
    ):
        ContentTypeGatingConfig.objects.create(
            enabled=True,
            enabled_as_of=datetime.datetime(2017, 1, 1, tzinfo=UTC),
        )
        course = self.courses[0]
        for mode in course_modes:
            CourseModeFactory.create(course_id=course.id, mode_slug=mode)

        enrollment = CourseEnrollment.objects.get(course_id=course.id, user=self.user)
        enrollment.mode = enrollment_mode
        enrollment.save()
        enrollment.schedule.start_date = timezone.now() - datetime.timedelta(days=30)
        enrollment.schedule.save()
        self.user.is_staff = is_course_staff
        self.user.save()

        url = course_home_url(course)
        response = self.client.get(url)

        if should_display:
            self.assertContains(response, '<div class="banner-cta-text"')
        else:
            self.assertNotContains(response, '<div class="banner-cta-text"')

    @override_experiment_waffle_flag(RELATIVE_DATES_FLAG, active=True)
    def test_reset_course_deadlines(self):
        course = self.courses[0]
        enrollment = CourseEnrollment.objects.get(course_id=course.id)
        enrollment.schedule.start_date = timezone.now() - datetime.timedelta(days=30)
        enrollment.schedule.save()

        student_schedule = CourseEnrollment.objects.get(course_id=course.id, user=self.user).schedule
        student_schedule.start_date = timezone.now() - datetime.timedelta(days=30)
        student_schedule.save()
        staff = StaffFactory(course_key=course.id)
        staff_schedule = ScheduleFactory(
            start_date=timezone.now() - datetime.timedelta(days=30),
            enrollment__course__id=course.id,
            enrollment__user=staff,
        )

        self.client.login(username=staff.username, password=TEST_PASSWORD)
        self.update_masquerade(course=course, username=self.user.username)

        post_dict = {'course_id': str(course.id)}
        self.client.post(reverse(RESET_COURSE_DEADLINES_NAME), post_dict)
        updated_schedule = Schedule.objects.get(id=student_schedule.id)
        self.assertEqual(updated_schedule.start_date.date(), datetime.datetime.today().date())
        updated_staff_schedule = Schedule.objects.get(id=staff_schedule.id)
        self.assertEqual(updated_staff_schedule.start_date, staff_schedule.start_date)

    @override_experiment_waffle_flag(RELATIVE_DATES_FLAG, active=True)
    def test_reset_course_deadlines_masquerade_generic_student(self):
        course = self.courses[0]

        student_schedule = CourseEnrollment.objects.get(course_id=course.id, user=self.user).schedule
        student_schedule.start_date = timezone.now() - datetime.timedelta(days=30)
        student_schedule.save()

        staff = StaffFactory(course_key=course.id)
        staff_schedule = ScheduleFactory(
            start_date=timezone.now() - datetime.timedelta(days=30),
            enrollment__course__id=course.id,
            enrollment__user=staff,
        )

        self.client.login(username=staff.username, password=TEST_PASSWORD)
        self.update_masquerade(course=course)

        post_dict = {'course_id': str(course.id)}
        self.client.post(reverse(RESET_COURSE_DEADLINES_NAME), post_dict)
        updated_student_schedule = Schedule.objects.get(id=student_schedule.id)
        self.assertEqual(updated_student_schedule.start_date, student_schedule.start_date)
        updated_staff_schedule = Schedule.objects.get(id=staff_schedule.id)
        self.assertEqual(updated_staff_schedule.start_date.date(), datetime.date.today())


class TestCourseOutlinePageWithPrerequisites(SharedModuleStoreTestCase, MilestonesTestCaseMixin):
    """
    Test the course outline view with prerequisites.
    """
    TRANSFORMER_CLASS_TO_TEST = MilestonesAndSpecialExamsTransformer

    @classmethod
    def setUpClass(cls):
        """
        Creates a test course that can be used for non-destructive tests
        """
        # pylint: disable=super-method-not-called

        cls.PREREQ_REQUIRED = '(Prerequisite required)'
        cls.UNLOCKED = 'Unlocked'

        with super(TestCourseOutlinePageWithPrerequisites, cls).setUpClassAndTestData():
            cls.course, cls.course_blocks = cls.create_test_course()

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.user = UserFactory(password=TEST_PASSWORD)
        CourseEnrollment.enroll(cls.user, cls.course.id)

    @classmethod
    def create_test_course(cls):
        """Creates a test course."""

        course = CourseFactory.create()
        course.enable_subsection_gating = True
        course_blocks = {}
        with cls.store.bulk_operations(course.id):
            course_blocks['chapter'] = ItemFactory.create(
                category='chapter',
                parent_location=course.location
            )
            course_blocks['prerequisite'] = ItemFactory.create(
                category='sequential',
                parent_location=course_blocks['chapter'].location,
                display_name='Prerequisite Exam'
            )
            course_blocks['gated_content'] = ItemFactory.create(
                category='sequential',
                parent_location=course_blocks['chapter'].location,
                display_name='Gated Content'
            )
            course_blocks['prerequisite_vertical'] = ItemFactory.create(
                category='vertical',
                parent_location=course_blocks['prerequisite'].location
            )
            course_blocks['gated_content_vertical'] = ItemFactory.create(
                category='vertical',
                parent_location=course_blocks['gated_content'].location
            )
        course.children = [course_blocks['chapter']]
        course_blocks['chapter'].children = [course_blocks['prerequisite'], course_blocks['gated_content']]
        course_blocks['prerequisite'].children = [course_blocks['prerequisite_vertical']]
        course_blocks['gated_content'].children = [course_blocks['gated_content_vertical']]
        if hasattr(cls, 'user'):
            CourseEnrollment.enroll(cls.user, course.id)
        return course, course_blocks

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseOutlinePageWithPrerequisites, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def setup_gated_section(self, gated_block, gating_block):
        """
        Test helper to create a gating requirement
        Args:
            gated_block: The block the that learner will not have access to until they complete the gating block
            gating_block: (The prerequisite) The block that must be completed to get access to the gated block
        """

        gating_api.add_prerequisite(self.course.id, six.text_type(gating_block.location))
        gating_api.set_required_content(self.course.id, gated_block.location, gating_block.location, 100)

    def test_content_locked(self):
        """
        Test that a sequential/subsection with unmet prereqs correctly indicated that its content is locked
        """
        course = self.course
        self.setup_gated_section(self.course_blocks['gated_content'], self.course_blocks['prerequisite'])

        response = self.client.get(course_home_url(course))
        self.assertEqual(response.status_code, 200)

        response_content = pq(response.content)

        # check lock icon is present
        lock_icon = response_content('.fa-lock')
        self.assertTrue(lock_icon, "lock icon is not present, but should be")

        subsection = lock_icon.parents('.subsection-text')

        # check that subsection-title-name is the display name
        gated_subsection_title = self.course_blocks['gated_content'].display_name
        self.assertIn(gated_subsection_title, subsection.children('.subsection-title').html())

        # check that it says prerequisite required
        self.assertIn("Prerequisite:", subsection.children('.details').html())

        # check that there is not a screen reader message
        self.assertFalse(subsection.children('.sr'))

    def test_content_unlocked(self):
        """
        Test that a sequential/subsection with met prereqs correctly indicated that its content is unlocked
        """
        course = self.course
        self.setup_gated_section(self.course_blocks['gated_content'], self.course_blocks['prerequisite'])

        # complete the prerequisite to unlock the gated content
        # this call triggers reevaluation of prerequisites fulfilled by the gating block.
        with patch('openedx.core.lib.gating.api.get_subsection_completion_percentage', Mock(return_value=100)):
            lms_gating_api.evaluate_prerequisite(
                self.course,
                Mock(location=self.course_blocks['prerequisite'].location, percent_graded=1.0),
                self.user,
            )

        response = self.client.get(course_home_url(course))
        self.assertEqual(response.status_code, 200)

        response_content = pq(response.content)

        # check unlock icon is not present
        unlock_icon = response_content('.fa-unlock')
        self.assertFalse(unlock_icon, "unlock icon is present, yet shouldn't be.")

        gated_subsection_title = self.course_blocks['gated_content'].display_name
        every_subsection_on_outline = response_content('.subsection-title')

        subsection_has_gated_text = False
        says_prerequisite_required = False

        for subsection_contents in every_subsection_on_outline.contents():
            subsection_has_gated_text = gated_subsection_title in subsection_contents
            says_prerequisite_required = "Prerequisite:" in subsection_contents

        # check that subsection-title-name is the display name of gated content section
        self.assertTrue(subsection_has_gated_text)
        self.assertFalse(says_prerequisite_required)


class TestCourseOutlineResumeCourse(SharedModuleStoreTestCase, CompletionWaffleTestMixin):
    """
    Test start course and resume course for the course outline view.

    Technically, this mixes course home and course outline tests, but checking
    the counts of start/resume course should be done together to avoid false
    positives.

    """
    @classmethod
    def setUpClass(cls):
        """
        Creates a test course that can be used for non-destructive tests
        """
        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super(TestCourseOutlineResumeCourse, cls).setUpClassAndTestData():
            cls.course = cls.create_test_course()

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.user = UserFactory(password=TEST_PASSWORD)
        CourseEnrollment.enroll(cls.user, cls.course.id)
        cls.site = Site.objects.get_current()

    @classmethod
    def create_test_course(cls):
        """
        Creates a test course.
        """
        course = CourseFactory.create()
        with cls.store.bulk_operations(course.id):
            chapter = ItemFactory.create(category='chapter', parent_location=course.location)
            chapter2 = ItemFactory.create(category='chapter', parent_location=course.location)
            sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
            sequential2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
            sequential3 = ItemFactory.create(category='sequential', parent_location=chapter2.location)
            sequential4 = ItemFactory.create(category='sequential', parent_location=chapter2.location)
            vertical = ItemFactory.create(category='vertical', parent_location=sequential.location)
            vertical2 = ItemFactory.create(category='vertical', parent_location=sequential2.location)
            vertical3 = ItemFactory.create(category='vertical', parent_location=sequential3.location)
            vertical4 = ItemFactory.create(category='vertical', parent_location=sequential4.location)
        course.children = [chapter, chapter2]
        chapter.children = [sequential, sequential2]
        chapter2.children = [sequential3, sequential4]
        sequential.children = [vertical]
        sequential2.children = [vertical2]
        sequential3.children = [vertical3]
        sequential4.children = [vertical4]
        if hasattr(cls, 'user'):
            CourseEnrollment.enroll(cls.user, course.id)
        return course

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseOutlineResumeCourse, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def visit_sequential(self, course, chapter, sequential):
        """
        Navigates to the provided sequential.
        """
        last_accessed_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': text_type(course.id),
                'chapter': chapter.url_name,
                'section': sequential.url_name,
            }
        )
        self.assertEqual(200, self.client.get(last_accessed_url).status_code)

    @override_switch(
        '{}.{}'.format(
            waffle.WAFFLE_NAMESPACE, waffle.ENABLE_COMPLETION_TRACKING
        ),
        active=True
    )
    def complete_sequential(self, course, sequential):
        """
        Completes provided sequential.
        """
        course_key = CourseKey.from_string(str(course.id))
        # Fake a visit to sequence2/vertical2
        block_key = UsageKey.from_string(six.text_type(sequential.location))
        if block_key.course_key.run is None:
            # Old mongo keys must be annotated with course run info before calling submit_completion:
            block_key = block_key.replace(course_key=course_key)
        completion = 1.0
        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=block_key,
            completion=completion
        )

    def visit_course_home(self, course, start_count=0, resume_count=0):
        """
        Helper function to navigates to course home page, test for resume buttons

        :param course: course factory object
        :param start_count: number of times 'Start Course' should appear
        :param resume_count: number of times 'Resume Course' should appear
        :return: response object
        """
        response = self.client.get(course_home_url(course))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Start Course', count=start_count)
        self.assertContains(response, 'Resume Course', count=resume_count)
        return response

    def test_course_home_completion(self):
        """
        Test that completed blocks appear checked on course home page
        """
        self.override_waffle_switch(True)

        course = self.course
        vertical = course.children[0].children[0].children[0]

        response = self.client.get(course_home_url(course))
        content = pq(response.content)
        self.assertEqual(len(content('.fa-check')), 0)

        self.complete_sequential(self.course, vertical)

        response = self.client.get(course_home_url(course))
        content = pq(response.content)

        # Subsection should be checked
        self.assertEqual(len(content('.fa-check')), 1)

    def test_start_course(self):
        """
        Tests that the start course button appears when the course has never been accessed.

        Technically, this is a course home test, and not a course outline test, but checking the counts of
        start/resume course should be done together to not get a false positive.

        """
        course = self.course

        response = self.visit_course_home(course, start_count=1, resume_count=0)
        content = pq(response.content)

        self.assertTrue(content('.action-resume-course').attr('href').endswith('/course/' + course.url_name))

    @override_settings(LMS_BASE='test_url:9999')
    def test_resume_course_with_completion_api(self):
        """
        Tests completion API resume button functionality
        """
        self.override_waffle_switch(True)

        # Course tree
        course = self.course
        vertical1 = course.children[0].children[0].children[0]
        vertical2 = course.children[0].children[1].children[0]

        self.complete_sequential(self.course, vertical1)
        # Test for 'resume' link
        response = self.visit_course_home(course, resume_count=1)

        # Test for 'resume' link URL - should be vertical 1
        content = pq(response.content)
        self.assertTrue(content('.action-resume-course').attr('href').endswith('/vertical/' + vertical1.url_name))

        self.complete_sequential(self.course, vertical2)
        # Test for 'resume' link
        response = self.visit_course_home(course, resume_count=1)

        # Test for 'resume' link URL - should be vertical 2
        content = pq(response.content)
        self.assertTrue(content('.action-resume-course').attr('href').endswith('/vertical/' + vertical2.url_name))

        # visit sequential 1, make sure 'Resume Course' URL is robust against 'Last Visited'
        # (even though I visited seq1/vert1, 'Resume Course' still points to seq2/vert2)
        self.visit_sequential(course, course.children[0], course.children[0].children[0])

        # Test for 'resume' link URL - should be vertical 2 (last completed block, NOT last visited)
        response = self.visit_course_home(course, resume_count=1)
        content = pq(response.content)
        self.assertTrue(content('.action-resume-course').attr('href').endswith('/vertical/' + vertical2.url_name))

    def test_resume_course_deleted_sequential(self):
        """
        Tests resume course when the last completed sequential is deleted and
        there is another sequential in the vertical.

        """
        course = self.create_test_course()

        # first navigate to a sequential to make it the last accessed
        chapter = course.children[0]
        self.assertGreaterEqual(len(chapter.children), 2)
        sequential = chapter.children[0]
        sequential2 = chapter.children[1]
        self.complete_sequential(course, sequential)
        self.complete_sequential(course, sequential2)

        # remove one of the sequentials from the chapter
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course.id):
            self.store.delete_item(sequential.location, self.user.id)

        # check resume course buttons
        response = self.visit_course_home(course, resume_count=1)

        content = pq(response.content)
        self.assertTrue(content('.action-resume-course').attr('href').endswith('/sequential/' + sequential2.url_name))

    def test_resume_course_deleted_sequentials(self):
        """
        Tests resume course when the last completed sequential is deleted and
        there are no sequentials left in the vertical.

        """
        course = self.create_test_course()

        # first navigate to a sequential to make it the last accessed
        chapter = course.children[0]
        self.assertEqual(len(chapter.children), 2)
        sequential = chapter.children[0]
        self.complete_sequential(course, sequential)

        # remove all sequentials from chapter
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course.id):
            for sequential in chapter.children:
                self.store.delete_item(sequential.location, self.user.id)

        # check resume course buttons
        self.visit_course_home(course, start_count=1, resume_count=0)

    def test_course_home_for_global_staff(self):
        """
        Tests that staff user can access the course home without being enrolled
        in the course.
        """
        course = self.course
        self.user.is_staff = True
        self.user.save()

        self.override_waffle_switch(True)
        CourseEnrollment.get_enrollment(self.user, course.id).delete()
        response = self.visit_course_home(course, start_count=1, resume_count=0)
        content = pq(response.content)
        self.assertTrue(content('.action-resume-course').attr('href').endswith('/course/' + course.url_name))

    @override_switch(
        '{}.{}'.format(
            waffle.WAFFLE_NAMESPACE, waffle.ENABLE_COMPLETION_TRACKING
        ),
        active=True
    )
    def test_course_outline_auto_open(self):
        """
        Tests that the course outline auto-opens to the first subsection
        in a course if a user has no completion data, and to the
        last-accessed subsection if a user does have completion data.
        """
        def get_sequential_button(url, is_hidden):
            is_hidden_string = "is-hidden" if is_hidden else ""

            return "<olclass=\"outline-itemaccordion-panel" + is_hidden_string + "\"" \
                   "id=\"" + url + "_contents\"" \
                   "aria-labelledby=\"" + url + "\"" \
                   ">"
        # Course tree
        course = self.course
        chapter1 = course.children[0]
        chapter2 = course.children[1]

        response_content = self.client.get(course_home_url(course)).content
        stripped_response = text_type(re.sub(b"\\s+", b"", response_content), "utf-8")

        self.assertIn(get_sequential_button(text_type(chapter1.location), False), stripped_response)
        self.assertIn(get_sequential_button(text_type(chapter2.location), True), stripped_response)

        content = pq(response_content)
        button = content('#expand-collapse-outline-all-button')
        self.assertEqual('Expand All', button.children()[0].text)

    def test_user_enrolled_after_completion_collection(self):
        """
        Tests that the _completion_data_collection_start() method returns the created
        time of the waffle switch that enables completion data tracking.
        """
        view = CourseOutlineFragmentView()
        switches = waffle.waffle()
        # pylint: disable=protected-access
        switch_name = switches._namespaced_name(waffle.ENABLE_COMPLETION_TRACKING)
        switch, _ = Switch.objects.get_or_create(name=switch_name)

        self.assertEqual(switch.created, view._completion_data_collection_start())

        switch.delete()

    def test_user_enrolled_after_completion_collection_default(self):
        """
        Tests that the _completion_data_collection_start() method returns a default constant
        when no Switch object exists for completion data tracking.
        """
        view = CourseOutlineFragmentView()

        # pylint: disable=protected-access
        self.assertEqual(DEFAULT_COMPLETION_TRACKING_START, view._completion_data_collection_start())


class TestCourseOutlinePreview(SharedModuleStoreTestCase, MasqueradeMixin):
    """
    Unit tests for staff preview of the course outline.
    """
    def test_preview(self):
        """
        Verify the behavior of preview for the course outline.
        """
        course = CourseFactory.create(
            start=datetime.datetime.now() - datetime.timedelta(days=30)
        )
        staff_user = StaffFactory(course_key=course.id, password=TEST_PASSWORD)
        CourseEnrollment.enroll(staff_user, course.id)

        future_date = datetime.datetime.now() + datetime.timedelta(days=30)
        with self.store.bulk_operations(course.id):
            chapter = ItemFactory.create(
                category='chapter',
                parent_location=course.location,
                display_name='First Chapter',
            )
            sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
            ItemFactory.create(category='vertical', parent_location=sequential.location)
            chapter = ItemFactory.create(
                category='chapter',
                parent_location=course.location,
                display_name='Future Chapter',
                start=future_date,
            )
            sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
            ItemFactory.create(category='vertical', parent_location=sequential.location)

        # Verify that a staff user sees a chapter with a due date in the future
        self.client.login(username=staff_user.username, password='test')
        url = course_home_url(course)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Future Chapter')

        # Verify that staff masquerading as a learner see the future chapter.
        self.update_masquerade(course=course, role='student')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Future Chapter')
