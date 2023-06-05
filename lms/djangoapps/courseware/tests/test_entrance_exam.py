"""
Tests use cases related to LMS Entrance Exam behavior, such as gated content access (TOC)
"""


import six
from crum import set_current_request
from django.urls import reverse
from milestones.tests.utils import MilestonesTestCaseMixin
from mock import Mock, patch

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.courseware.entrance_exams import (
    course_has_entrance_exam,
    get_entrance_exam_content,
    user_can_skip_entrance_exam,
    user_has_passed_entrance_exam
)
from lms.djangoapps.courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.module_render import get_module, handle_xblock_callback, toc_for_course
from lms.djangoapps.courseware.tests.factories import InstructorFactory, RequestFactoryNoCsrf, StaffFactory, UserFactory
from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase
from openedx.core.djangolib.testing.utils import get_mock_request
from openedx.features.course_experience import DISABLE_COURSE_OUTLINE_PAGE_FLAG, DISABLE_UNIFIED_COURSE_TAB_FLAG
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import AnonymousUserFactory, CourseEnrollmentFactory
from common.djangoapps.util.milestones_helpers import (
    add_course_content_milestone,
    add_course_milestone,
    add_milestone,
    generate_milestone_namespace,
    get_milestone_relationship_types,
    get_namespace_choices
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@patch.dict('django.conf.settings.FEATURES', {'ENTRANCE_EXAMS': True})
class EntranceExamTestCases(LoginEnrollmentTestCase, ModuleStoreTestCase, MilestonesTestCaseMixin):
    """
    Check that content is properly gated.

    Creates a test course from scratch. The tests below are designed to execute
    workflows regardless of the feature flag settings.
    """

    @patch.dict('django.conf.settings.FEATURES', {'ENTRANCE_EXAMS': True})
    def setUp(self):
        """
        Test case scaffolding
        """
        super(EntranceExamTestCases, self).setUp()
        self.course = CourseFactory.create(
            metadata={
                'entrance_exam_enabled': True,
            }
        )
        with self.store.bulk_operations(self.course.id):
            self.chapter = ItemFactory.create(
                parent=self.course,
                display_name='Overview'
            )
            self.welcome = ItemFactory.create(
                parent=self.chapter,
                display_name='Welcome'
            )
            ItemFactory.create(
                parent=self.course,
                category='chapter',
                display_name="Week 1"
            )
            self.chapter_subsection = ItemFactory.create(
                parent=self.chapter,
                category='sequential',
                display_name="Lesson 1"
            )
            chapter_vertical = ItemFactory.create(
                parent=self.chapter_subsection,
                category='vertical',
                display_name='Lesson 1 Vertical - Unit 1'
            )
            ItemFactory.create(
                parent=chapter_vertical,
                category="problem",
                display_name="Problem - Unit 1 Problem 1"
            )
            ItemFactory.create(
                parent=chapter_vertical,
                category="problem",
                display_name="Problem - Unit 1 Problem 2"
            )

            ItemFactory.create(
                category="instructor",
                parent=self.course,
                data="Instructor Tab",
                display_name="Instructor"
            )
            self.entrance_exam = ItemFactory.create(
                parent=self.course,
                category="chapter",
                display_name="Entrance Exam Section - Chapter 1",
                is_entrance_exam=True,
                in_entrance_exam=True
            )
            self.exam_1 = ItemFactory.create(
                parent=self.entrance_exam,
                category='sequential',
                display_name="Exam Sequential - Subsection 1",
                graded=True,
                in_entrance_exam=True
            )
            subsection = ItemFactory.create(
                parent=self.exam_1,
                category='vertical',
                display_name='Exam Vertical - Unit 1'
            )
            problem_xml = MultipleChoiceResponseXMLFactory().build_xml(
                question_text='The correct answer is Choice 3',
                choices=[False, False, True, False],
                choice_names=['choice_0', 'choice_1', 'choice_2', 'choice_3']
            )
            self.problem_1 = ItemFactory.create(
                parent=subsection,
                category="problem",
                display_name="Exam Problem - Problem 1",
                data=problem_xml
            )
            self.problem_2 = ItemFactory.create(
                parent=subsection,
                category="problem",
                display_name="Exam Problem - Problem 2"
            )

        add_entrance_exam_milestone(self.course, self.entrance_exam)

        self.course.entrance_exam_enabled = True
        self.course.entrance_exam_minimum_score_pct = 0.50
        self.course.entrance_exam_id = six.text_type(self.entrance_exam.scope_ids.usage_id)

        self.anonymous_user = AnonymousUserFactory()
        self.addCleanup(set_current_request, None)
        self.request = get_mock_request(UserFactory())
        modulestore().update_item(self.course, self.request.user.id)

        self.client.login(username=self.request.user.username, password="test")
        CourseEnrollment.enroll(self.request.user, self.course.id)

        self.expected_locked_toc = (
            [
                {
                    'active': True,
                    'sections': [
                        {
                            'url_name': u'Exam_Sequential_-_Subsection_1',
                            'display_name': u'Exam Sequential - Subsection 1',
                            'graded': True,
                            'format': '',
                            'due': None,
                            'active': True
                        }
                    ],
                    'url_name': u'Entrance_Exam_Section_-_Chapter_1',
                    'display_name': u'Entrance Exam Section - Chapter 1',
                    'display_id': u'entrance-exam-section-chapter-1',
                }
            ]
        )
        self.expected_unlocked_toc = (
            [
                {
                    'active': False,
                    'sections': [
                        {
                            'url_name': u'Welcome',
                            'display_name': u'Welcome',
                            'graded': False,
                            'format': '',
                            'due': None,
                            'active': False
                        },
                        {
                            'url_name': u'Lesson_1',
                            'display_name': u'Lesson 1',
                            'graded': False,
                            'format': '',
                            'due': None,
                            'active': False
                        }
                    ],
                    'url_name': u'Overview',
                    'display_name': u'Overview',
                    'display_id': u'overview'
                },
                {
                    'active': False,
                    'sections': [],
                    'url_name': u'Week_1',
                    'display_name': u'Week 1',
                    'display_id': u'week-1'
                },
                {
                    'active': False,
                    'sections': [],
                    'url_name': u'Instructor',
                    'display_name': u'Instructor',
                    'display_id': u'instructor'
                },
                {
                    'active': True,
                    'sections': [
                        {
                            'url_name': u'Exam_Sequential_-_Subsection_1',
                            'display_name': u'Exam Sequential - Subsection 1',
                            'graded': True,
                            'format': '',
                            'due': None,
                            'active': True
                        }
                    ],
                    'url_name': u'Entrance_Exam_Section_-_Chapter_1',
                    'display_name': u'Entrance Exam Section - Chapter 1',
                    'display_id': u'entrance-exam-section-chapter-1'
                }
            ]
        )

    def test_view_redirect_if_entrance_exam_required(self):
        """
        Unit Test: if entrance exam is required. Should return a redirect.
        """
        url = reverse('courseware', kwargs={'course_id': six.text_type(self.course.id)})
        expected_url = reverse('courseware_section',
                               kwargs={
                                   'course_id': six.text_type(self.course.id),
                                   'chapter': self.entrance_exam.location.block_id,
                                   'section': self.exam_1.location.block_id
                               })
        resp = self.client.get(url)
        self.assertRedirects(resp, expected_url, status_code=302, target_status_code=200)

    @patch.dict('django.conf.settings.FEATURES', {'ENTRANCE_EXAMS': False})
    def test_entrance_exam_content_absence(self):
        """
        Unit Test: If entrance exam is not enabled then page should be redirected with chapter contents.
        """
        url = reverse('courseware', kwargs={'course_id': six.text_type(self.course.id)})
        expected_url = reverse('courseware_section',
                               kwargs={
                                   'course_id': six.text_type(self.course.id),
                                   'chapter': self.chapter.location.block_id,
                                   'section': self.welcome.location.block_id
                               })
        resp = self.client.get(url)
        self.assertRedirects(resp, expected_url, status_code=302, target_status_code=200)
        resp = self.client.get(expected_url)
        self.assertNotContains(resp, 'Exam Vertical - Unit 1')

    def test_entrance_exam_content_presence(self):
        """
        Unit Test: If entrance exam is enabled then its content e.g. problems should be loaded and redirection will
        occur with entrance exam contents.
        """
        url = reverse('courseware', kwargs={'course_id': six.text_type(self.course.id)})
        expected_url = reverse('courseware_section',
                               kwargs={
                                   'course_id': six.text_type(self.course.id),
                                   'chapter': self.entrance_exam.location.block_id,
                                   'section': self.exam_1.location.block_id
                               })
        resp = self.client.get(url)
        self.assertRedirects(resp, expected_url, status_code=302, target_status_code=200)
        resp = self.client.get(expected_url)
        self.assertContains(resp, 'Exam Vertical - Unit 1')

    def test_get_entrance_exam_content(self):
        """
        test get entrance exam content method
        """
        exam_chapter = get_entrance_exam_content(self.request.user, self.course)
        self.assertEqual(exam_chapter.url_name, self.entrance_exam.url_name)
        self.assertFalse(user_has_passed_entrance_exam(self.request.user, self.course))

        answer_entrance_exam_problem(self.course, self.request, self.problem_1)
        answer_entrance_exam_problem(self.course, self.request, self.problem_2)

        exam_chapter = get_entrance_exam_content(self.request.user, self.course)
        self.assertEqual(exam_chapter, None)
        self.assertTrue(user_has_passed_entrance_exam(self.request.user, self.course))

    def test_entrance_exam_requirement_message(self):
        """
        Unit Test: entrance exam requirement message should be present in response
        """
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': six.text_type(self.course.id),
                'chapter': self.entrance_exam.location.block_id,
                'section': self.exam_1.location.block_id,
            }
        )
        resp = self.client.get(url)
        self.assertContains(resp, 'To access course materials, you must score')

    def test_entrance_exam_requirement_message_with_correct_percentage(self):
        """
        Unit Test: entrance exam requirement message should be present in response
        and percentage of required score should be rounded as expected
        """
        minimum_score_pct = 29
        self.course.entrance_exam_minimum_score_pct = float(minimum_score_pct) / 100
        modulestore().update_item(self.course, self.request.user.id)

        # answer the problem so it results in only 20% correct.
        answer_entrance_exam_problem(self.course, self.request, self.problem_1, value=1, max_value=5)

        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': six.text_type(self.course.id),
                'chapter': self.entrance_exam.location.block_id,
                'section': self.exam_1.location.block_id
            }
        )
        resp = self.client.get(url)
        self.assertContains(
            resp,
            u'To access course materials, you must score {}% or higher'.format(minimum_score_pct),
        )
        self.assertIn(u'Your current score is 20%.', resp.content.decode(resp.charset))

    def test_entrance_exam_requirement_message_hidden(self):
        """
        Unit Test: entrance exam message should not be present outside the context of entrance exam subsection.
        """
        # Login as staff to avoid redirect to entrance exam
        self.client.logout()
        staff_user = StaffFactory(course_key=self.course.id)
        self.client.login(username=staff_user.username, password='test')
        CourseEnrollment.enroll(staff_user, self.course.id)

        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': six.text_type(self.course.id),
                'chapter': self.chapter.location.block_id,
                'section': self.chapter_subsection.location.block_id
            }
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'To access course materials, you must score')
        self.assertNotContains(resp, 'You have passed the entrance exam.')

    # TODO: LEARNER-71: Do we need to adjust or remove this test?
    @override_waffle_flag(DISABLE_COURSE_OUTLINE_PAGE_FLAG, active=True)
    def test_entrance_exam_passed_message_and_course_content(self):
        """
        Unit Test: exam passing message and rest of the course section should be present
        when user achieves the entrance exam milestone/pass the exam.
        """
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': six.text_type(self.course.id),
                'chapter': self.entrance_exam.location.block_id,
                'section': self.exam_1.location.block_id
            }
        )

        answer_entrance_exam_problem(self.course, self.request, self.problem_1)
        answer_entrance_exam_problem(self.course, self.request, self.problem_2)

        resp = self.client.get(url)
        self.assertNotContains(resp, 'To access course materials, you must score')
        self.assertContains(resp, u'Your score is 100%. You have passed the entrance exam.')
        self.assertContains(resp, 'Lesson 1')

    def test_entrance_exam_gating(self):
        """
        Unit Test: test_entrance_exam_gating
        """
        # This user helps to cover a discovered bug in the milestone fulfillment logic
        chaos_user = UserFactory()
        locked_toc = self._return_table_of_contents()
        for toc_section in self.expected_locked_toc:
            self.assertIn(toc_section, locked_toc)

        # Set up the chaos user
        answer_entrance_exam_problem(self.course, self.request, self.problem_1, chaos_user)
        answer_entrance_exam_problem(self.course, self.request, self.problem_1)
        answer_entrance_exam_problem(self.course, self.request, self.problem_2)

        unlocked_toc = self._return_table_of_contents()

        for toc_section in self.expected_unlocked_toc:
            self.assertIn(toc_section, unlocked_toc)

    def test_skip_entrance_exam_gating(self):
        """
        Tests gating is disabled if skip entrance exam is set for a user.
        """
        # make sure toc is locked before allowing user to skip entrance exam
        locked_toc = self._return_table_of_contents()
        for toc_section in self.expected_locked_toc:
            self.assertIn(toc_section, locked_toc)

        # hit skip entrance exam api in instructor app
        instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=instructor.username, password='test')
        url = reverse('mark_student_can_skip_entrance_exam', kwargs={'course_id': six.text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.request.user.email,
        })
        self.assertEqual(response.status_code, 200)

        unlocked_toc = self._return_table_of_contents()
        for toc_section in self.expected_unlocked_toc:
            self.assertIn(toc_section, unlocked_toc)

    def test_entrance_exam_gating_for_staff(self):
        """
        Tests gating is disabled if user is member of staff.
        """

        # Login as member of staff
        self.client.logout()
        staff_user = StaffFactory(course_key=self.course.id)
        staff_user.is_staff = True
        self.client.login(username=staff_user.username, password='test')

        # assert staff has access to all toc
        self.request.user = staff_user
        unlocked_toc = self._return_table_of_contents()
        for toc_section in self.expected_unlocked_toc:
            self.assertIn(toc_section, unlocked_toc)

    def test_courseware_page_access_without_passing_entrance_exam(self):
        """
        Test courseware access page without passing entrance exam
        """
        url = reverse(
            'courseware_chapter',
            kwargs={'course_id': six.text_type(self.course.id), 'chapter': self.chapter.url_name}
        )
        response = self.client.get(url)
        expected_url = reverse('courseware_section',
                               kwargs={
                                   'course_id': six.text_type(self.course.id),
                                   'chapter': self.entrance_exam.location.block_id,
                                   'section': self.exam_1.location.block_id
                               })
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)

    @override_waffle_flag(DISABLE_UNIFIED_COURSE_TAB_FLAG, active=True)
    def test_courseinfo_page_access_without_passing_entrance_exam(self):
        """
        Test courseware access page without passing entrance exam
        """
        url = reverse('info', args=[six.text_type(self.course.id)])
        response = self.client.get(url)
        redirect_url = reverse('courseware', args=[six.text_type(self.course.id)])
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=302)
        response = self.client.get(redirect_url)
        exam_url = response.get('Location')
        self.assertRedirects(response, exam_url)

    @patch('lms.djangoapps.courseware.entrance_exams.get_entrance_exam_content', Mock(return_value=None))
    def test_courseware_page_access_after_passing_entrance_exam(self):
        """
        Test courseware access page after passing entrance exam
        """
        self._assert_chapter_loaded(self.course, self.chapter)

    @patch('common.djangoapps.util.milestones_helpers.get_required_content', Mock(return_value=['a value']))
    def test_courseware_page_access_with_staff_user_without_passing_entrance_exam(self):
        """
        Test courseware access page without passing entrance exam but with staff user
        """
        self.logout()
        staff_user = StaffFactory.create(course_key=self.course.id)
        self.login(staff_user.email, 'test')
        CourseEnrollmentFactory(user=staff_user, course_id=self.course.id)
        self._assert_chapter_loaded(self.course, self.chapter)

    def test_courseware_page_access_with_staff_user_after_passing_entrance_exam(self):
        """
        Test courseware access page after passing entrance exam but with staff user
        """
        self.logout()
        staff_user = StaffFactory.create(course_key=self.course.id)
        self.login(staff_user.email, 'test')
        CourseEnrollmentFactory(user=staff_user, course_id=self.course.id)
        self._assert_chapter_loaded(self.course, self.chapter)

    @patch.dict("django.conf.settings.FEATURES", {'ENTRANCE_EXAMS': False})
    def test_courseware_page_access_when_entrance_exams_disabled(self):
        """
        Test courseware page access when ENTRANCE_EXAMS feature is disabled
        """
        self._assert_chapter_loaded(self.course, self.chapter)

    def test_can_skip_entrance_exam_with_anonymous_user(self):
        """
        Test can_skip_entrance_exam method with anonymous user
        """
        self.assertFalse(user_can_skip_entrance_exam(self.anonymous_user, self.course))

    def test_has_passed_entrance_exam_with_anonymous_user(self):
        """
        Test has_passed_entrance_exam method with anonymous user
        """
        self.request.user = self.anonymous_user
        self.assertFalse(user_has_passed_entrance_exam(self.request.user, self.course))

    def test_course_has_entrance_exam_missing_exam_id(self):
        course = CourseFactory.create(
            metadata={
                'entrance_exam_enabled': True,
            }
        )
        self.assertFalse(course_has_entrance_exam(course))

    def test_user_has_passed_entrance_exam_short_circuit_missing_exam(self):
        course = CourseFactory.create(
        )
        self.assertTrue(user_has_passed_entrance_exam(self.request.user, course))

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_MASQUERADE': False})
    def test_entrance_exam_xblock_response(self):
        """
        Tests entrance exam xblock has `entrance_exam_passed` key in json response.
        """
        request_factory = RequestFactoryNoCsrf()
        data = {'input_{}_2_1'.format(six.text_type(self.problem_1.location.html_id())): 'choice_2'}
        request = request_factory.post(
            'problem_check',
            data=data
        )
        request.user = self.user
        response = handle_xblock_callback(
            request,
            six.text_type(self.course.id),
            six.text_type(self.problem_1.location),
            'xmodule_handler',
            'problem_check',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'entrance_exam_passed')

    def _assert_chapter_loaded(self, course, chapter):
        """
        Asserts courseware chapter load successfully.
        """
        url = reverse(
            'courseware_chapter',
            kwargs={'course_id': six.text_type(course.id), 'chapter': chapter.url_name}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def _return_table_of_contents(self):
        """
        Returns table of content for the entrance exam specific to this test

        Returns the table of contents for course self.course, for chapter
        self.entrance_exam, and for section self.exam1
        """
        self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(  # pylint: disable=attribute-defined-outside-init
            self.course.id,
            self.request.user,
            self.entrance_exam
        )
        toc = toc_for_course(
            self.request.user,
            self.request,
            self.course,
            self.entrance_exam.url_name,
            self.exam_1.url_name,
            self.field_data_cache
        )
        return toc['chapters']


def answer_entrance_exam_problem(course, request, problem, user=None, value=1, max_value=1):
    """
    Takes a required milestone `problem` in a `course` and fulfills it.

    Args:
        course (Course): Course object, the course the required problem is in
        request (Request): request Object
        problem (xblock): xblock object, the problem to be fulfilled
        user (User): User object in case it is different from request.user
        value (int): raw_earned value of the problem
        max_value (int): raw_possible value of the problem
    """
    if not user:
        user = request.user

    grade_dict = {'value': value, 'max_value': max_value, 'user_id': user.id}
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id,
        user,
        course,
        depth=2
    )
    module = get_module(
        user,
        request,
        problem.scope_ids.usage_id,
        field_data_cache,
    )
    module.system.publish(problem, 'grade', grade_dict)


def add_entrance_exam_milestone(course, entrance_exam):
    """
    Adds the milestone for given `entrance_exam` in `course`

    Args:
        course (Course): Course object in which the extrance_exam is located
        entrance_exam (xblock): the entrance exam to be added as a milestone
    """
    namespace_choices = get_namespace_choices()
    milestone_relationship_types = get_milestone_relationship_types()

    milestone_namespace = generate_milestone_namespace(
        namespace_choices.get('ENTRANCE_EXAM'),
        course.id
    )
    milestone = add_milestone(
        {
            'name': 'Test Milestone',
            'namespace': milestone_namespace,
            'description': 'Testing Courseware Entrance Exam Chapter',
        }
    )
    add_course_milestone(
        six.text_type(course.id),
        milestone_relationship_types['REQUIRES'],
        milestone
    )
    add_course_content_milestone(
        six.text_type(course.id),
        six.text_type(entrance_exam.location),
        milestone_relationship_types['FULFILLS'],
        milestone
    )
