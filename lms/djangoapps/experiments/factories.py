import factory

from experiments.models import ExperimentData
from student.tests.factories import UserFactory


class ExperimentDataFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ExperimentData

    user = factory.SubFactory(UserFactory)
    experiment_id = factory.fuzzy.FuzzyInteger(0)
    key = factory.Sequence(lambda n: n)
    value = factory.Faker('word')
