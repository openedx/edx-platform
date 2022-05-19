"""
Tests for courseware services.
"""


from functools import partial
import itertools
import json
from unittest.mock import Mock

import ddt

from xmodule.contentstore.django import contentstore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.courseware.module_render import get_module_for_descriptor_internal
from lms.djangoapps.courseware.services import ModuleService, UserStateService
from lms.djangoapps.courseware.tests.factories import StudentModuleFactory


@ddt.ddt
class TestUserStateService(ModuleStoreTestCase):
    """
    Test suite for user state service.
    """

    def setUp(self):
        """
        Creating pre-requisites for the test cases.
        """
        super().setUp()
        self.user = UserFactory.create()
        self.course = CourseFactory.create()
        chapter = ItemFactory.create(
            category='chapter',
            parent=self.course,
            display_name='Test Chapter'
        )
        sequential = ItemFactory.create(
            category='sequential',
            parent=chapter,
            display_name='Test Sequential'
        )
        vertical = ItemFactory.create(
            category='vertical',
            parent=sequential,
            display_name='Test Vertical'
        )
        self.problem = ItemFactory.create(
            category='problem',
            parent=vertical,
            display_name='Test Problem'
        )

    def _create_student_module(self, state):
        StudentModuleFactory.create(
            student=self.user,
            module_state_key=self.problem.location,
            course_id=self.course.id,
            state=json.dumps(state)
        )

    def _get_email_or_username(self, should_use_email):
        """
        Helper function that returns either username or email of the user based on given criteria.

        Arguments:
            should_use_email(bool): Flag to identify if the email is to be returned
        Returns:
            username/email depending upon the value of provided flag
        """
        return self.user.email if should_use_email else self.user.username

    @ddt.data(
        *itertools.product(
            [
                ({'key_1a': 'value_1a', 'key_2a': 'value_2a'}),
                ({'key_1b': 'value_1b', 'key_2b': 'value_2b', 'key_3b': 'value_3b'})
            ], [
                True, False
            ]
        ))
    @ddt.unpack
    def test_student_state(self, expected_state, should_use_email):
        """
        Verify the service gets the correct state from the student module.

        Scenario:
            Given a user and a problem or block
            Then create a student module entry for the user
            If the state is obtained from common.djangoapps.student module service
            Then the state is equal to previously created student module state
        """
        self._create_student_module(expected_state)
        state = UserStateService().get_state_as_dict(
            self._get_email_or_username(should_use_email), self.problem.location
        )
        self.assertDictEqual(state, expected_state)

    @ddt.data(
        *itertools.product(
            [
                ({'username_or_email': 'no_user', 'block_id':
                    'block-v1:myOrg+123+2030_T2+type@openassessment+block@hash'}),
                ({'username_or_email': 'no_user'}),
                ({'block_id': 'block-v1:myOrg+1234+2030_T2+type@openassessment+block@hash'})
            ], [
                True, False
            ]
        ))
    @ddt.unpack
    def test_nonexistent_student_module_state(self, state_params, should_use_email):
        """
        Verify the user state service returns empty dict for non-existent student module entry.

        Scenario:
            Given a user and a problem/block
            Then create a student module entry for the user
            If the state is obtained with incorrect parameters
            Then an empty dict is returned
        """
        params = {
            'username_or_email': self._get_email_or_username(should_use_email),
            'block_id': self.problem.location
        }
        params.update(state_params)
        self._create_student_module({'key_1': 'value_1'})
        state = UserStateService().get_state_as_dict(**params)
        assert not state


class TestModuleService(SharedModuleStoreTestCase):
    """
    Tests the Module Service.
    """
    COURSE_ID = 'edX/LmsModuleShimTest/2021_Fall'

    @classmethod
    def setUpClass(cls):
        """
        Set up the course and descriptor used to instantiate the runtime.
        """
        super().setUpClass()
        org, number, run = cls.COURSE_ID.split('/')
        cls.course = CourseFactory.create(org=org, number=number, run=run)
        cls.descriptor = ItemFactory(category="vertical", parent=cls.course)

    def setUp(self):
        """
        Set up the user and other fields that will be used to instantiate the runtime.
        """
        super().setUp()
        self.user = UserFactory(id=232)
        self.student_data = Mock()
        self.track_function = Mock()
        self.request_token = Mock()
        self.contentstore = contentstore()
        self.module = get_module_for_descriptor_internal(
            user=self.user,
            descriptor=self.descriptor,
            student_data=self.student_data,
            course_id=self.course.id,
            track_function=self.track_function,
            request_token=self.request_token,
            course=self.course
        )

    def test_get_module(self):
        """
        Test the get_module method of ModuleService
        """
        module_service = ModuleService(partial(
            get_module_for_descriptor_internal,
            user=self.user,
            student_data=self.student_data,
            course_id=self.course.id,
            track_function=self.track_function,
            request_token=self.request_token,
            course=self.course
        ))
        assert module_service.get_module(self.descriptor) == self.module
