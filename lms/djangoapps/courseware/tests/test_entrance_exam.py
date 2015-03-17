"""
Tests use cases related to LMS Entrance Exam behavior, such as gated content access (TOC)
"""
from django.conf import settings
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module, toc_for_course
from courseware.tests.factories import UserFactory, InstructorFactory
from courseware.courses import get_entrance_exam_content_info, get_entrance_exam_score
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from util import milestones_helpers
from student.models import CourseEnrollment
from mock import patch
import mock


class EntranceExamTestCases(ModuleStoreTestCase):
    """
    Check that content is properly gated.  Create a test course from scratch to mess with.
    We typically assume that the Entrance Exam feature flag is set to True in test.py
    However, the tests below are designed to execute workflows regardless of the setting
    If set to False, we are essentially confirming that the workflows do not cause exceptions
    """
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
        self.chapter = ItemFactory.create(
            parent=self.course,
            display_name='Overview'
        )
        ItemFactory.create(
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
        self.problem_1 = ItemFactory.create(
            parent=subsection,
            category="problem",
            display_name="Exam Problem - Problem 1"
        )
        self.problem_2 = ItemFactory.create(
            parent=subsection,
            category="problem",
            display_name="Exam Problem - Problem 2"
        )
        self.problem_3 = ItemFactory.create(
            parent=subsection,
            category="problem",
            display_name="Exam Problem - Problem 3"
        )
        if settings.FEATURES.get('ENTRANCE_EXAMS', False):
            namespace_choices = milestones_helpers.get_namespace_choices()
            milestone_namespace = milestones_helpers.generate_milestone_namespace(
                namespace_choices.get('ENTRANCE_EXAM'),
                self.course.id
            )
            self.milestone = {
                'name': 'Test Milestone',
                'namespace': milestone_namespace,
                'description': 'Testing Courseware Entrance Exam Chapter',
            }
            milestones_helpers.seed_milestone_relationship_types()
            self.milestone_relationship_types = milestones_helpers.get_milestone_relationship_types()
            self.milestone = milestones_helpers.add_milestone(self.milestone)
            milestones_helpers.add_course_milestone(
                unicode(self.course.id),
                self.milestone_relationship_types['REQUIRES'],
                self.milestone
            )
            milestones_helpers.add_course_content_milestone(
                unicode(self.course.id),
                unicode(self.entrance_exam.location),
                self.milestone_relationship_types['FULFILLS'],
                self.milestone
            )
        user = UserFactory()
        self.request = RequestFactory()
        self.request.user = user
        self.request.COOKIES = {}
        self.request.META = {}
        self.request.is_secure = lambda: True
        self.request.get_host = lambda: "edx.org"
        self.request.method = 'GET'
        self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            user,
            self.entrance_exam
        )
        self.course.entrance_exam_enabled = True
        self.course.entrance_exam_minimum_score_pct = 0.50
        self.course.entrance_exam_id = unicode(self.entrance_exam.scope_ids.usage_id)
        modulestore().update_item(self.course, user.id)  # pylint: disable=no-member

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
                    'display_name': u'Entrance Exam Section - Chapter 1'
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
                    'display_name': u'Overview'
                },
                {
                    'active': False,
                    'sections': [],
                    'url_name': u'Week_1',
                    'display_name': u'Week 1'
                },
                {
                    'active': False,
                    'sections': [],
                    'url_name': u'Instructor',
                    'display_name': u'Instructor'
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
                    'display_name': u'Entrance Exam Section - Chapter 1'
                }
            ]
        )

    @mock.patch('xmodule.x_module.XModuleMixin.has_dynamic_children', mock.Mock(return_value='True'))
    def test_view_redirect_if_entrance_exam_required(self):
        """
        Unit Test: if entrance exam is required. Should return a redirect.
        """
        url = reverse('courseware', kwargs={'course_id': unicode(self.course.id)})
        expected_url = reverse('courseware_section',
                               kwargs={
                                   'course_id': unicode(self.course.id),
                                   'chapter': self.entrance_exam.location.name,
                                   'section': self.exam_1.location.name
                               })
        resp = self.client.get(url)
        if settings.FEATURES.get('ENTRANCE_EXAMS', False):
            self.assertRedirects(resp, expected_url, status_code=302, target_status_code=200)

    @patch.dict('django.conf.settings.FEATURES', {'ENTRANCE_EXAMS': False})
    def test_entrance_exam_content_absence(self):
        """
        Unit Test: If entrance exam is not enabled then page should be redirected with chapter contents.
        """
        url = reverse('courseware', kwargs={'course_id': unicode(self.course.id)})
        expected_url = reverse('courseware_section',
                               kwargs={
                                   'course_id': unicode(self.course.id),
                                   'chapter': self.chapter.location.name,
                                   'section': self.chapter_subsection.location.name
                               })
        resp = self.client.get(url)
        self.assertRedirects(resp, expected_url, status_code=302, target_status_code=200)
        resp = self.client.get(expected_url)
        self.assertNotIn('Exam Problem - Problem 1', resp.content)
        self.assertNotIn('Exam Problem - Problem 2', resp.content)

    def test_entrance_exam_content_presence(self):
        """
        Unit Test: If entrance exam is enabled then its content e.g. problems should be loaded and redirection will
        occur with entrance exam contents.
        """
        url = reverse('courseware', kwargs={'course_id': unicode(self.course.id)})
        expected_url = reverse('courseware_section',
                               kwargs={
                                   'course_id': unicode(self.course.id),
                                   'chapter': self.entrance_exam.location.name,
                                   'section': self.exam_1.location.name
                               })
        resp = self.client.get(url)
        if settings.FEATURES.get('ENTRANCE_EXAMS', False):
            self.assertRedirects(resp, expected_url, status_code=302, target_status_code=200)
            resp = self.client.get(expected_url)
            self.assertIn('Exam Problem - Problem 1', resp.content)
            self.assertIn('Exam Problem - Problem 2', resp.content)

    def test_entrance_exam_content_info(self):
        """
        test entrance exam content info method
        """
        exam_chapter, is_exam_passed = get_entrance_exam_content_info(self.request, self.course)
        if settings.FEATURES.get('ENTRANCE_EXAMS', False):
            self.assertEqual(exam_chapter.url_name, self.entrance_exam.url_name)
            self.assertEqual(is_exam_passed, False)

            # Pass the entrance exam
            # pylint: disable=maybe-no-member,no-member
            grade_dict = {'value': 1, 'max_value': 1, 'user_id': self.request.user.id}
            field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
                self.course.id,
                self.request.user,
                self.course,
                depth=2
            )
            # pylint: disable=protected-access
            module = get_module(
                self.request.user,
                self.request,
                self.problem_1.scope_ids.usage_id,
                field_data_cache,
            )._xmodule
            module.system.publish(self.problem_1, 'grade', grade_dict)

            exam_chapter, is_exam_passed = get_entrance_exam_content_info(self.request, self.course)
            self.assertEqual(exam_chapter, None)
            self.assertEqual(is_exam_passed, True)

    @patch.dict('django.conf.settings.FEATURES', {'ENTRANCE_EXAMS': True})
    def test_entrance_exam_score(self):
        """
        test entrance exam score. we will hit the method get_entrance_exam_score to verify exam score.
        """
        exam_score = get_entrance_exam_score(self.request, self.course)
        self.assertEqual(exam_score, 0)

        # Pass the entrance exam
        # pylint: disable=maybe-no-member,no-member
        grade_dict = {'value': 1, 'max_value': 2, 'user_id': self.request.user.id}
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.request.user,
            self.course,
            depth=2
        )
        # pylint: disable=protected-access
        module = get_module(
            self.request.user,
            self.request,
            self.problem_1.scope_ids.usage_id,
            field_data_cache,
        )._xmodule
        module.system.publish(self.problem_1, 'grade', grade_dict)

        exam_score = get_entrance_exam_score(self.request, self.course)
        # 50 percent exam score should be achieved.
        self.assertEqual(exam_score * 100, 50)

    def test_entrance_exam_requirement_message(self):
        """
        Unit Test: entrance exam requirement message should be present in response
        """
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': unicode(self.course.id),
                'chapter': self.entrance_exam.location.name,
                'section': self.exam_1.location.name
            }
        )
        resp = self.client.get(url)
        if settings.FEATURES.get('ENTRANCE_EXAMS', False):
            self.assertEqual(resp.status_code, 200)
            self.assertIn('To access course materials, you must score', resp.content)

    def test_entrance_exam_requirement_message_hidden(self):
        """
        Unit Test: entrance exam message should not be present outside the context of entrance exam subsection.
        """
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': unicode(self.course.id),
                'chapter': self.chapter.location.name,
                'section': self.chapter_subsection.location.name
            }
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        if settings.FEATURES.get('ENTRANCE_EXAMS', False):
            self.assertNotIn('To access course materials, you must score', resp.content)
            self.assertNotIn('You have passed the entrance exam.', resp.content)

    def test_entrance_exam_passed_message_and_course_content(self):
        """
        Unit Test: exam passing message and rest of the course section should be present
        when user achieves the entrance exam milestone/pass the exam.
        """
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': unicode(self.course.id),
                'chapter': self.entrance_exam.location.name,
                'section': self.exam_1.location.name
            }
        )

        # pylint: disable=maybe-no-member,no-member
        grade_dict = {'value': 1, 'max_value': 1, 'user_id': self.request.user.id}
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.request.user,
            self.course,
            depth=2
        )
        # pylint: disable=protected-access
        module = get_module(
            self.request.user,
            self.request,
            self.problem_1.scope_ids.usage_id,
            field_data_cache,
        )._xmodule
        module.system.publish(self.problem_1, 'grade', grade_dict)

        resp = self.client.get(url)
        if settings.FEATURES.get('ENTRANCE_EXAMS', False):
            self.assertNotIn('To access course materials, you must score', resp.content)
            self.assertIn('You have passed the entrance exam.', resp.content)
            self.assertIn('Lesson 1', resp.content)

    @patch.dict('django.conf.settings.FEATURES', {'ENTRANCE_EXAMS': True})
    def test_entrance_exam_gating(self):
        """
        Unit Test: test_entrance_exam_gating
        """
        # This user helps to cover a discovered bug in the milestone fulfillment logic
        chaos_user = UserFactory()
        locked_toc = toc_for_course(
            self.request,
            self.course,
            self.entrance_exam.url_name,
            self.exam_1.url_name,
            self.field_data_cache
        )
        for toc_section in self.expected_locked_toc:
            self.assertIn(toc_section, locked_toc)

        # Set up the chaos user
        # pylint: disable=maybe-no-member,no-member
        grade_dict = {'value': 1, 'max_value': 1, 'user_id': chaos_user.id}
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            chaos_user,
            self.course,
            depth=2
        )
        # pylint: disable=protected-access
        module = get_module(
            chaos_user,
            self.request,
            self.problem_1.scope_ids.usage_id,
            field_data_cache,
        )._xmodule
        module.system.publish(self.problem_1, 'grade', grade_dict)

        # pylint: disable=maybe-no-member,no-member
        grade_dict = {'value': 1, 'max_value': 1, 'user_id': self.request.user.id}
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.request.user,
            self.course,
            depth=2
        )
        # pylint: disable=protected-access
        module = get_module(
            self.request.user,
            self.request,
            self.problem_1.scope_ids.usage_id,
            field_data_cache,
        )._xmodule
        module.system.publish(self.problem_1, 'grade', grade_dict)

        module = get_module(
            self.request.user,
            self.request,
            self.problem_2.scope_ids.usage_id,
            field_data_cache,
        )._xmodule  # pylint: disable=protected-access
        module.system.publish(self.problem_2, 'grade', grade_dict)
        unlocked_toc = toc_for_course(
            self.request,
            self.course,
            self.entrance_exam.url_name,
            self.exam_1.url_name,
            self.field_data_cache
        )

        for toc_section in self.expected_unlocked_toc:
            self.assertIn(toc_section, unlocked_toc)

    @patch.dict('django.conf.settings.FEATURES', {'ENTRANCE_EXAMS': True})
    def test_skip_entrance_exame_gating(self):
        """
        Tests gating is disabled if skip entrance exam is set for a user.
        """
        # make sure toc is locked before allowing user to skip entrance exam
        locked_toc = toc_for_course(
            self.request,
            self.course,
            self.entrance_exam.url_name,
            self.exam_1.url_name,
            self.field_data_cache
        )
        for toc_section in self.expected_locked_toc:
            self.assertIn(toc_section, locked_toc)

        # hit skip entrance exam api in instructor app
        instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=instructor.username, password='test')
        url = reverse('mark_student_can_skip_entrance_exam', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.request.user.email,
        })
        self.assertEqual(response.status_code, 200)

        unlocked_toc = toc_for_course(
            self.request,
            self.course,
            self.entrance_exam.url_name,
            self.exam_1.url_name,
            self.field_data_cache
        )
        for toc_section in self.expected_unlocked_toc:
            self.assertIn(toc_section, unlocked_toc)
