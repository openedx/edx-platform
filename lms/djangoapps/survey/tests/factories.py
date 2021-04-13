# lint-amnesty, pylint: disable=missing-module-docstring
from factory.django import DjangoModelFactory

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.survey.models import SurveyAnswer, SurveyForm


class SurveyFormFactory(DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta:
        model = SurveyForm

    name = 'Test Survey Form'
    form = '<form>First name:<input type="text" name="firstname"/></form>'


class SurveyAnswerFactory(DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta:
        model = SurveyAnswer

    user = factory.SubFactory(UserFactory)
    form = factory.SubFactory(SurveyFormFactory)
