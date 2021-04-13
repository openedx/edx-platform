"""
Experimentation factories
"""


import factory.fuzzy
from factory.django import DjangoModelFactory

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.experiments.models import ExperimentData, ExperimentKeyValue


class ExperimentDataFactory(DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta:
        model = ExperimentData

    user = factory.SubFactory(UserFactory)
    experiment_id = factory.fuzzy.FuzzyInteger(0)
    key = factory.Sequence(lambda n: n)
    value = factory.Faker('word')


class ExperimentKeyValueFactory(DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta:
        model = ExperimentKeyValue

    experiment_id = factory.fuzzy.FuzzyInteger(0)
    key = factory.Sequence(lambda n: n)
    value = factory.Faker('word')
