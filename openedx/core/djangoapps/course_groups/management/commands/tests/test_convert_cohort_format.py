"""
Tests to make sure the convert_cohort_format command works correctly.
"""
from ddt import unpack, data, ddt
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from openedx.core.djangoapps.course_groups.management.commands.convert_cohort_format import Command


@ddt
class TestConvertCohortFormat(ModuleStoreTestCase):
    """
    Make sure the format is converted correctly.
    """

    @unpack
    @data(
        ({'unrelated_setting': False, 'inline_discussions_cohorting_default': True}, {
            'unrelated_setting': False, 'inline_discussions_cohorting_default': True,
            'always_cohort_inline_discussions': True,
        }),
        ({'unrelated_setting': False}, {'unrelated_setting': False}),
        (None, {})
    )
    def test_convert_format(self, course_config, result):
        if course_config:
            course = CourseFactory(metadata={'cohort_config': course_config})
        else:
            course = CourseFactory()
        Command().handle()
        # pylint: disable=no-member
        course = modulestore().get_course(course.location.course_key)
        self.assertEqual(
            course.cohort_config, result)
