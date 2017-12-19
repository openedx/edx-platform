"""Factories for generating fake credentials-related data."""
# pylint: disable=missing-docstring, invalid-name
from functools import partial

import factory

from openedx.core.djangoapps.catalog.tests.factories import DictFactoryBase, generate_course_run_key, generate_instances


class ProgramCredential(DictFactoryBase):
    credential_id = factory.Faker('random_int')
    program_uuid = factory.Faker('uuid4')


class CourseCredential(DictFactoryBase):
    credential_id = factory.Faker('random_int')
    course_id = factory.LazyFunction(generate_course_run_key)
    certificate_type = 'verified'


class UserCredential(DictFactoryBase):
    id = factory.Faker('random_int')
    username = factory.Faker('word')
    status = 'awarded'
    uuid = factory.Faker('uuid4')
    certificate_url = factory.Faker('url')
    credential = factory.LazyFunction(partial(generate_instances, ProgramCredential, count=1))
