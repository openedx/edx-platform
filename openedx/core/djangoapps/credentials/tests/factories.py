"""Factories for generating fake credentials-related data."""
# pylint: disable=missing-docstring, invalid-name


import factory

from openedx.core.djangoapps.catalog.tests.factories import DictFactoryBase, generate_course_run_key


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
    credential = ProgramCredential()


class UserCredentialsCourseRunStatus(DictFactoryBase):
    course_uuid = str(factory.Faker('uuid4'))
    course_run = {
        "uuid": str(factory.Faker('uuid4')),
        "key": factory.LazyFunction(generate_course_run_key)
    }
    status = 'awarded'
    type = 'verified'
    certificate_available_date = factory.Faker('date')
    grade = None
