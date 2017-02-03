"""Factories for generating fake credentials-related data."""
import uuid

import factory
from factory.fuzzy import FuzzyText


class UserCredential(factory.Factory):
    """Factory for stubbing user credentials resources from the User Credentials
    API (v1).
    """
    class Meta(object):
        model = dict

    id = factory.Sequence(lambda n: n)  # pylint: disable=invalid-name
    username = FuzzyText(prefix='user_')
    status = 'awarded'
    uuid = FuzzyText(prefix='uuid_')
    certificate_url = FuzzyText(prefix='https://www.example.com/credentials/')
    credential = {}


class ProgramCredential(factory.Factory):
    """Factory for stubbing program credentials resources from the Program
    Credentials API (v1).
    """
    class Meta(object):
        model = dict

    credential_id = factory.Sequence(lambda n: n)
    program_uuid = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))


class CourseCredential(factory.Factory):
    """Factory for stubbing course credentials resources from the Course
    Credentials API (v1).
    """
    class Meta(object):
        model = dict

    course_id = 'edx/test01/2015'
    credential_id = factory.Sequence(lambda n: n)
    certificate_type = 'verified'
