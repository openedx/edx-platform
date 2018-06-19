"""
Test signal handlers for the survey app
"""

from student.tests.factories import UserFactory
from survey.models import SurveyAnswer
from survey.tests.factories import SurveyAnswerFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from ..signals import _listen_for_lms_retire


class SurveyRetireSignalTests(ModuleStoreTestCase):
    """
    Test the _listen_for_lms_retire signal
    """
    shard = 4

    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        super(SurveyRetireSignalTests, self).setUp()

    def test_success_answers_exist(self):
        answer = SurveyAnswerFactory(field_value="test value")

        _listen_for_lms_retire(sender=self.__class__, user=answer.user)

        # All values for this user should now be empty string
        self.assertFalse(SurveyAnswer.objects.filter(user=answer.user).exclude(field_value='').exists())

    def test_success_no_answers(self):
        user = UserFactory()

        # All we care about is that this does not throw an error
        _listen_for_lms_retire(sender=self.__class__, user=user)

    def test_idempotent(self):
        answer = SurveyAnswerFactory(field_value="test value")

        # Run twice to make sure no errors are raised
        _listen_for_lms_retire(sender=self.__class__, user=answer.user)
        _listen_for_lms_retire(sender=self.__class__, user=answer.user)

        # All values for this user should still be empty string
        self.assertFalse(SurveyAnswer.objects.filter(user=answer.user).exclude(field_value='').exists())
