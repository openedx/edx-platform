"""Factories for generating fake program-related data."""
# pylint: disable=missing-docstring, invalid-name
import factory
from faker import Faker


fake = Faker()


class ProgressFactory(factory.Factory):
    class Meta(object):
        model = dict

    uuid = factory.Faker('uuid4')
    completed = []
    in_progress = []
    not_started = []
