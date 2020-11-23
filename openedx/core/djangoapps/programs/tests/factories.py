"""Factories for generating fake program-related data."""
# pylint: disable=missing-docstring


import factory


class ProgressFactory(factory.Factory):
    class Meta(object):
        model = dict

    uuid = factory.Faker('uuid4')
    completed = 0
    in_progress = 0
    not_started = 0
