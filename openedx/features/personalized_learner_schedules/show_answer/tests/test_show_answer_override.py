"""Tests for Show Answer overrides for self-paced courses."""

import ddt
from django.test import RequestFactory
from django.test.utils import override_settings

from common.lib.xmodule.xmodule.capa_base import SHOWANSWER
from lms.djangoapps.ccx.tests.test_overrides import inject_field_overrides
from lms.djangoapps.courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.module_render import get_module
from lms.djangoapps.experiments.testutils import override_experiment_waffle_flag
from openedx.features.course_experience import RELATIVE_DATES_FLAG
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@override_settings(
    FIELD_OVERRIDE_PROVIDERS=[
        'openedx.features.personalized_learner_schedules.show_answer.show_answer_field_override.ShowAnswerFieldOverride'
    ],
)
@ddt.ddt
class ShowAnswerFieldOverrideTest(ModuleStoreTestCase):
    """ Tests for Show Answer overrides for self-paced courses. """

    def setup_course(self, **course_kwargs):
        """ Set up a course with provided course attributes. """
        course = CourseFactory.create(**course_kwargs)
        inject_field_overrides((course,), course, self.user)
        return course

    def get_course_module(self, course):
        request = RequestFactory().request()
        field_data_cache = FieldDataCache([], course.id, self.user)
        return get_module(self.user, request, course.location, field_data_cache, course=course)

    @ddt.data(True, False)
    def test_override_enabled_for(self, active):
        with override_experiment_waffle_flag(RELATIVE_DATES_FLAG, active=active):
            # Instructor paced course will just have the default value
            ip_course = self.setup_course()
            course_module = self.get_course_module(ip_course)
            self.assertEqual(course_module.showanswer, SHOWANSWER.FINISHED)

            # This should be updated to not explicitly add in the showanswer so it can test the
            # default case of never touching showanswer. Reference ticket AA-307 (if that's closed,
            # this can be updated!)
            sp_course = self.setup_course(self_paced=True, showanswer=SHOWANSWER.FINISHED)
            course_module = self.get_course_module(sp_course)
            if active:
                self.assertEqual(course_module.showanswer, SHOWANSWER.AFTER_ALL_ATTEMPTS_OR_CORRECT)
            else:
                self.assertEqual(course_module.showanswer, SHOWANSWER.FINISHED)

    @ddt.data(
        (SHOWANSWER.ATTEMPTED, SHOWANSWER.ATTEMPTED_NO_PAST_DUE),
        (SHOWANSWER.CLOSED, SHOWANSWER.AFTER_ALL_ATTEMPTS),
        (SHOWANSWER.CORRECT_OR_PAST_DUE, SHOWANSWER.ANSWERED),
        (SHOWANSWER.FINISHED, SHOWANSWER.AFTER_ALL_ATTEMPTS_OR_CORRECT),
        (SHOWANSWER.PAST_DUE, SHOWANSWER.NEVER),
        (SHOWANSWER.NEVER, SHOWANSWER.NEVER),
        (SHOWANSWER.AFTER_SOME_NUMBER_OF_ATTEMPTS, SHOWANSWER.AFTER_SOME_NUMBER_OF_ATTEMPTS),
        (SHOWANSWER.ALWAYS, SHOWANSWER.ALWAYS),
    )
    @ddt.unpack
    @override_experiment_waffle_flag(RELATIVE_DATES_FLAG, active=True)
    def test_get(self, initial_value, expected_final_value):
        course = self.setup_course(self_paced=True, showanswer=initial_value)
        course_module = self.get_course_module(course)
        self.assertEqual(course_module.showanswer, expected_final_value)
