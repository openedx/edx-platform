"""
Tests for OverrideDataTransformer.
"""
import datetime

import ddt
import pytz
from courseware.student_field_overrides import get_override_for_user, override_field_for_user
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory

from lms.djangoapps.course_blocks.transformers.load_override_data import REQUESTED_FIELDS, OverrideDataTransformer
from openedx.core.djangoapps.content.block_structure.factory import BlockStructureFactory

expected_overrides = {
    'start': datetime.datetime(
        2017, 1, 20, 2, 42, tzinfo=pytz.UTC
    ),
    'display_name': "Section",
    'due': datetime.datetime(
        2017, 2, 20, 2, 42, tzinfo=pytz.UTC
    )
}


@ddt.ddt
class TestOverrideDataTransformer(ModuleStoreTestCase):
    """
    Test proper behavior for OverrideDataTransformer
    """
    @classmethod
    def setUpClass(cls):
        super(TestOverrideDataTransformer, cls).setUpClass()
        cls.learner = UserFactory.create(password="test")

    def setUp(self):
        super(TestOverrideDataTransformer, self).setUp()
        self.course_key = ToyCourseFactory.create().id
        self.course_usage_key = self.store.make_course_usage_key(self.course_key)
        self.block_structure = BlockStructureFactory.create_from_modulestore(self.course_usage_key, self.store)
        self.course = course = modulestore().get_course(self.course_key)
        section = course.get_children()[0]
        subsection = section.get_children()[0]
        self.block = self.store.create_child(
            self.learner.id, subsection.location, 'html', 'new_component'
        )
        CourseEnrollmentFactory.create(user=self.learner, course_id=self.course_key, is_active=True)

    @ddt.data(*REQUESTED_FIELDS)
    def test_transform(self, field):
        override_field_for_user(
            self.learner,
            self.block,
            field,
            expected_overrides.get(field)
        )

        # collect phase
        OverrideDataTransformer.collect(self.block_structure)

        # transform phase
        OverrideDataTransformer().transform(
            usage_info=self.course_usage_key,
            block_structure=self.block_structure,
        )

        # verify overridden data
        assert get_override_for_user(self.learner, self.block, field) == expected_overrides.get(field)

    def test_transform_all_fields(self):
        """Test overriding of all fields"""
        for field in REQUESTED_FIELDS:
            override_field_for_user(
                self.learner,
                self.block,
                field,
                expected_overrides.get(field)
            )

        # collect phase
        OverrideDataTransformer.collect(self.block_structure)

        # transform phase
        OverrideDataTransformer().transform(
            usage_info=self.course_usage_key,
            block_structure=self.block_structure,
        )

        # verify overridden data
        for field in REQUESTED_FIELDS:
            assert get_override_for_user(self.learner, self.block, field) == expected_overrides.get(field)
