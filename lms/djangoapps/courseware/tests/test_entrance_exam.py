"""
Tests use cases related to LMS Entrance Exam behavior, such as gated content access (TOC)
"""
from django.test.client import RequestFactory
from django.test.utils import override_settings

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module, toc_for_course
from courseware.tests.factories import UserFactory
from milestones import api as milestones_api
from milestones.models import MilestoneRelationshipType
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_MOCK_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from util.milestones_helpers import generate_milestone_namespace, NAMESPACE_CHOICES


class EntranceExamTestCases(ModuleStoreTestCase):
    """
    Check that content is properly gated.  Create a test course from scratch to mess with.
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
        chapter = ItemFactory.create(
            parent=self.course,
            display_name='Overview'
        )
        ItemFactory.create(
            parent=chapter,
            display_name='Welcome'
        )
        ItemFactory.create(
            parent=self.course,
            category='chapter',
            display_name="Week 1"
        )
        ItemFactory.create(
            parent=chapter,
            category='sequential',
            display_name="Lesson 1"
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
            display_name="Entrance Exam Section - Chapter 1"
        )
        self.exam_1 = ItemFactory.create(
            parent=self.entrance_exam,
            category='sequential',
            display_name="Exam Sequential - Subsection 1",
            graded=True,
            metadata={'in_entrance_exam': True}
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
        milestone_namespace = generate_milestone_namespace(
            NAMESPACE_CHOICES['ENTRANCE_EXAM'],
            self.course.id
        )
        self.milestone = {
            'name': 'Test Milestone',
            'namespace': milestone_namespace,
            'description': 'Testing Courseware Entrance Exam Chapter',
        }
        MilestoneRelationshipType.objects.create(name='requires', active=True)
        MilestoneRelationshipType.objects.create(name='fulfills', active=True)
        self.milestone_relationship_types = milestones_api.get_milestone_relationship_types()
        self.milestone = milestones_api.add_milestone(self.milestone)
        milestones_api.add_course_milestone(
            unicode(self.course.id),
            self.milestone_relationship_types['REQUIRES'],
            self.milestone
        )
        milestones_api.add_course_content_milestone(
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
        self.entrance_exam.is_entrance_exam = True
        self.entrance_exam.in_entrance_exam = True
        self.course.entrance_exam_enabled = True
        self.course.entrance_exam_minimum_score_pct = 0.50
        self.course.entrance_exam_id = unicode(self.entrance_exam.scope_ids.usage_id)
        modulestore().update_item(self.course, user.id)  # pylint: disable=no-member

    def test_entrance_exam_gating(self):
        """
        Unit Test: test_entrance_exam_gating
        """
        # This user helps to cover a discovered bug in the milestone fulfillment logic
        chaos_user = UserFactory()
        expected_locked_toc = (
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
        locked_toc = toc_for_course(
            self.request,
            self.course,
            self.entrance_exam.url_name,
            self.exam_1.url_name,
            self.field_data_cache
        )
        for toc_section in expected_locked_toc:
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

        expected_unlocked_toc = (
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

        unlocked_toc = toc_for_course(
            self.request,
            self.course,
            self.entrance_exam.url_name,
            self.exam_1.url_name,
            self.field_data_cache
        )

        for toc_section in expected_unlocked_toc:
            self.assertIn(toc_section, unlocked_toc)
