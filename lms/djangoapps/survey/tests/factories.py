import factory  # lint-amnesty, pylint: disable=missing-module-docstring

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.survey.models import SurveyAnswer, SurveyForm


class SurveyFormFactory(factory.DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta(object):
        model = SurveyForm

    name = 'Test Survey Form'
    form = '<form>First name:<input type="text" name="firstname"/></form>'


class SurveyAnswerFactory(factory.DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta(object):
        model = SurveyAnswer

    user = factory.SubFactory(UserFactory)
    form = factory.SubFactory(SurveyFormFactory)
