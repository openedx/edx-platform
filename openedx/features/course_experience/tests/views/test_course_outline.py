"""
Tests for the Course Outline view and supporting views.
"""
import datetime
import json
import re

from completion import waffle
from completion.models import BlockCompletion
from completion.test_utils import CompletionWaffleTestMixin
from django.contrib.sites.models import Site
from django.urls import reverse
from django.test import override_settings
from mock import Mock, patch
from six import text_type
from waffle.models import Switch
from waffle.testutils import override_switch

from courseware.tests.factories import StaffFactory
from gating import api as lms_gating_api
from lms.djangoapps.course_api.blocks.transformers.milestones import MilestonesAndSpecialExamsTransformer
from milestones.tests.utils import MilestonesTestCaseMixin
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx.core.lib.gating import api as gating_api
from openedx.features.course_experience.views.course_outline import (
    CourseOutlineFragmentView, DEFAULT_COMPLETION_TRACKING_START
)
from pyquery import PyQuery as pq
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from .test_course_home import course_home_url

TEST_PASSWORD = 'test'
GATING_NAMESPACE_QUALIFIER = '.gating'


class TestCourseOutlinePage(SharedModuleStoreTestCase):
    """
    Test the course outline view.
    """
    @classmethod
    def setUpClass(cls):
        """
        Set up an array of various courses to be tested.
        """
        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super(TestCourseOutlinePage, cls).setUpClassAndTestData():
            cls.courses = []
            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
                vertical = ItemFactory.create(category='vertical', parent_location=sequential.location)
            course.children = [chapter]
            chapter.children = [sequential]
            sequential.children = [vertical]
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
            CourseEnrollment.enroll(cls.user, course.id)

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseOutlinePage, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def test_outline_details(self):
        for course in self.courses:

            url = course_home_url(course)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            response_content = response.content.decode("utf-8")

            self.assertTrue(course.children)
            for chapter in course.children:
                self.assertIn(chapter.display_name, response_content)
                self.assertTrue(chapter.children)
                for sequential in chapter.children:
                    self.assertIn(sequential.display_name, response_content)
                    if sequential.graded:
                        self.assertIn(sequential.due.strftime('%Y-%m-%d %H:%M:%S'), response_content)
                        self.assertIn(sequential.format, response_content)
                    self.assertTrue(sequential.children)
                    for vertical in sequential.children:
                        self.assertIn(vertical.display_name, response_content)


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

        gating_api.add_prerequisite(self.course.id, unicode(gating_block.location))
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
            sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
            sequential2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
            vertical = ItemFactory.create(category='vertical', parent_location=sequential.location)
            vertical2 = ItemFactory.create(category='vertical', parent_location=sequential2.location)
        course.children = [chapter]
        chapter.children = [sequential, sequential2]
        sequential.children = [vertical]
        sequential2.children = [vertical2]
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
        block_key = UsageKey.from_string(unicode(sequential.location))
        completion = 1.0
        BlockCompletion.objects.submit_completion(
            user=self.user,
            course_key=course_key,
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

        # vertical and its parent should be checked
        self.assertEqual(len(content('.fa-check')), 2)

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
        course_key = CourseKey.from_string(str(course.id))
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
        Tests that the course outline auto-opens to the first unit
        in a course if a user has no completion data, and to the
        last-accessed unit if a user does have completion data.
        """
        def get_sequential_button(url, is_hidden):
            is_hidden_string = "is-hidden" if is_hidden else ""

            return "<olclass=\"outline-itemaccordion-panel" + is_hidden_string + "\"" \
                   "id=\"" + url + "_contents\"" \
                   "aria-labelledby=\"" + url + "\"" \
                   ">"
        # Course tree
        course = self.course
        chapter = course.children[0]
        sequential1 = chapter.children[0]
        sequential2 = chapter.children[1]

        response_content = self.client.get(course_home_url(course)).content
        stripped_response = text_type(re.sub("\\s+", "", response_content), "utf-8")

        self.assertTrue(get_sequential_button(text_type(sequential1.location), False) in stripped_response)
        self.assertTrue(get_sequential_button(text_type(sequential2.location), True) in stripped_response)

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


class TestCourseOutlinePreview(SharedModuleStoreTestCase):
    """
    Unit tests for staff preview of the course outline.
    """
    def update_masquerade(self, course, role, group_id=None, user_name=None):
        """
        Toggle masquerade state.
        """
        masquerade_url = reverse(
            'masquerade_update',
            kwargs={
                'course_key_string': unicode(course.id),
            }
        )
        response = self.client.post(
            masquerade_url,
            json.dumps({'role': role, 'group_id': group_id, 'user_name': user_name}),
            'application/json'
        )
        self.assertEqual(response.status_code, 200)
        return response

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
        self.update_masquerade(course, role='student')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Future Chapter')
