"""Tests for Show Answer overrides for self-paced courses."""

import ddt
from django.test import RequestFactory
from django.test.utils import override_settings

from edx_toggles.toggles.testutils import override_waffle_flag

from lms.djangoapps.ccx.tests.test_overrides import inject_field_overrides
from lms.djangoapps.courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.block_render import get_block
from openedx.features.course_experience import RELATIVE_DATES_FLAG
from xmodule.graders import ShowAnswer
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


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

    def get_course_block(self, course):
        request = RequestFactory().request()
        field_data_cache = FieldDataCache([], course.id, self.user)
        return get_block(self.user, request, course.location, field_data_cache, course=course)

    @ddt.data(True, False)
    def test_override_enabled_for(self, active):
        with override_waffle_flag(RELATIVE_DATES_FLAG, active=active):
            # Instructor paced course will just have the default value
            ip_course = self.setup_course()
            course_block = self.get_course_block(ip_course)
            assert course_block.showanswer == ShowAnswer.FINISHED

            # This should be updated to not explicitly add in the showanswer so it can test the
            # default case of never touching showanswer. Reference ticket AA-307 (if that's closed,
            # this can be updated!)
            sp_course = self.setup_course(self_paced=True, showanswer=ShowAnswer.FINISHED)
            course_block = self.get_course_block(sp_course)
            if active:
                assert course_block.showanswer == ShowAnswer.AFTER_ALL_ATTEMPTS_OR_CORRECT
            else:
                assert course_block.showanswer == ShowAnswer.FINISHED

    @ddt.data(
        (ShowAnswer.ATTEMPTED, ShowAnswer.ATTEMPTED_NO_PAST_DUE),
        (ShowAnswer.CLOSED, ShowAnswer.AFTER_ALL_ATTEMPTS),
        (ShowAnswer.CORRECT_OR_PAST_DUE, ShowAnswer.ANSWERED),
        (ShowAnswer.FINISHED, ShowAnswer.AFTER_ALL_ATTEMPTS_OR_CORRECT),
        (ShowAnswer.PAST_DUE, ShowAnswer.NEVER),
        (ShowAnswer.NEVER, ShowAnswer.NEVER),
        (ShowAnswer.AFTER_SOME_NUMBER_OF_ATTEMPTS, ShowAnswer.AFTER_SOME_NUMBER_OF_ATTEMPTS),
        (ShowAnswer.ALWAYS, ShowAnswer.ALWAYS),
    )
    @ddt.unpack
    @override_waffle_flag(RELATIVE_DATES_FLAG, active=True)
    def test_get(self, initial_value, expected_final_value):
        course = self.setup_course(self_paced=True, showanswer=initial_value)
        course_block = self.get_course_block(course)
        assert course_block.showanswer == expected_final_value
