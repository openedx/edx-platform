"""Factories for generating fake program-related data."""
# pylint: disable=missing-docstring, invalid-name
import factory
from faker import Faker


class ProgressFactory(factory.Factory):
    class Meta(object):
        model = dict

    uuid = factory.Faker('uuid4')
    completed = 0
    in_progress = 0
    not_started = 0
