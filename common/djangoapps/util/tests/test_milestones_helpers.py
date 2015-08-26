"""
Tests for the milestones helpers library, which is the integration point for the edx_milestones API
"""

from mock import patch

from milestones.exceptions import InvalidCourseKeyException, InvalidUserException
from util import milestones_helpers
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@patch.dict('django.conf.settings.FEATURES', {'MILESTONES_APP': False})
class MilestonesHelpersTestCase(ModuleStoreTestCase):
    """
    Main test suite for Milestones API client library
    """

    def setUp(self):
        """
        Test case scaffolding
        """
        super(MilestonesHelpersTestCase, self).setUp(create_user=False)
        self.course = CourseFactory.create(
            metadata={
                'entrance_exam_enabled': True,
            }
        )

        self.user = {'id': '123'}

        self.milestone = {
            'name': 'Test Milestone',
            'namespace': 'doesnt.matter',
            'description': 'Testing Milestones Helpers Library',
        }

    def test_add_milestone_returns_none_when_app_disabled(self):
        response = milestones_helpers.add_milestone(milestone_data=self.milestone)
        self.assertIsNone(response)

    def test_get_milestones_returns_none_when_app_disabled(self):
        response = milestones_helpers.get_milestones(namespace="whatever")
        self.assertEqual(len(response), 0)

    def test_get_milestone_relationship_types_returns_none_when_app_disabled(self):
        response = milestones_helpers.get_milestone_relationship_types()
        self.assertEqual(len(response), 0)

    def test_add_course_milestone_returns_none_when_app_disabled(self):
        response = milestones_helpers.add_course_milestone(unicode(self.course.id), 'requires', self.milestone)
        self.assertIsNone(response)

    def test_get_course_milestones_returns_none_when_app_disabled(self):
        response = milestones_helpers.get_course_milestones(unicode(self.course.id))
        self.assertEqual(len(response), 0)

    def test_add_course_content_milestone_returns_none_when_app_disabled(self):
        response = milestones_helpers.add_course_content_milestone(
            unicode(self.course.id),
            'i4x://any/content/id',
            'requires',
            self.milestone
        )
        self.assertIsNone(response)

    def test_get_course_content_milestones_returns_none_when_app_disabled(self):
        response = milestones_helpers.get_course_content_milestones(
            unicode(self.course.id),
            'i4x://doesnt/matter/for/this/test',
            'requires'
        )
        self.assertEqual(len(response), 0)

    def test_remove_content_references_returns_none_when_app_disabled(self):
        response = milestones_helpers.remove_content_references("i4x://any/content/id/will/do")
        self.assertIsNone(response)

    def test_get_namespace_choices_returns_values_when_app_disabled(self):
        response = milestones_helpers.get_namespace_choices()
        self.assertIn('ENTRANCE_EXAM', response)

    def test_get_course_milestones_fulfillment_paths_returns_none_when_app_disabled(self):
        response = milestones_helpers.get_course_milestones_fulfillment_paths(unicode(self.course.id), self.user)
        self.assertIsNone(response)

    def test_add_user_milestone_returns_none_when_app_disabled(self):
        response = milestones_helpers.add_user_milestone(self.user, self.milestone)
        self.assertIsNone(response)

    @patch.dict('django.conf.settings.FEATURES', {'MILESTONES_APP': True})
    def test_any_unfulfilled_milestones(self):
        """ Tests any_unfulfilled_milestones for invalid arguments """
        with self.assertRaises(InvalidCourseKeyException):
            milestones_helpers.any_unfulfilled_milestones(None, self.user)
        with self.assertRaises(InvalidUserException):
            milestones_helpers.any_unfulfilled_milestones(self.course.id, None)
