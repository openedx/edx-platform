"""Factories for generating fake catalog data."""
# pylint: disable=missing-docstring, invalid-name
from random import randint

import factory
from faker import Faker


fake = Faker()


def generate_course_key():
    return '+'.join(fake.words(2))


def generate_course_run_key():
    return 'course-v1:' + '+'.join(fake.words(3))


def generate_zulu_datetime():
    """
    The catalog returns UTC datetimes formatted using Z, the zone designator
    for the zero UTC offset, not the +00:00 offset. For more, see
    https://en.wikipedia.org/wiki/ISO_8601#UTC.
    """
    return fake.date_time().isoformat() + 'Z'


class DictFactory(factory.Factory):
    class Meta(object):
        model = dict


class ImageFactory(DictFactory):
    height = factory.Faker('random_int')
    width = factory.Faker('random_int')


class Image(ImageFactory):
    """
    For constructing dicts mirroring the catalog's serialized representation of ImageFields.

    See https://github.com/edx/course-discovery/blob/master/course_discovery/apps/api/fields.py.
    """
    description = factory.Faker('sentence')
    src = factory.Faker('image_url')


class StdImage(ImageFactory):
    """
    For constructing dicts mirroring the catalog's serialized representation of StdImageFields.

    See https://github.com/edx/course-discovery/blob/master/course_discovery/apps/api/fields.py.
    """
    url = factory.Faker('image_url')


def generate_sized_stdimage():
    return {
        size: StdImage() for size in ['large', 'medium', 'small', 'x-small']
    }


class Organization(DictFactory):
    key = factory.Faker('word')
    name = factory.Faker('company')
    uuid = factory.Faker('uuid4')


class CourseRun(DictFactory):
    end = factory.LazyFunction(generate_zulu_datetime)
    enrollment_end = factory.LazyFunction(generate_zulu_datetime)
    enrollment_start = factory.LazyFunction(generate_zulu_datetime)
    image = Image()
    key = factory.LazyFunction(generate_course_run_key)
    marketing_url = factory.Faker('url')
    pacing_type = 'self_paced'
    short_description = factory.Faker('sentence')
    start = factory.LazyFunction(generate_zulu_datetime)
    title = factory.Faker('catch_phrase')
    type = 'verified'
    uuid = factory.Faker('uuid4')


class Course(DictFactory):
    course_runs = [CourseRun() for __ in range(randint(3, 5))]
    image = Image()
    key = factory.LazyFunction(generate_course_key)
    owners = [Organization()]
    title = factory.Faker('catch_phrase')
    uuid = factory.Faker('uuid4')


class Program(DictFactory):
    authoring_organizations = [Organization()]
    banner_image = factory.LazyFunction(generate_sized_stdimage)
    card_image_url = factory.Faker('image_url')
    courses = [Course() for __ in range(randint(3, 5))]
    marketing_slug = factory.Faker('slug')
    marketing_url = factory.Faker('url')
    status = 'active'
    subtitle = factory.Faker('sentence')
    title = factory.Faker('catch_phrase')
    type = factory.Faker('word')
    uuid = factory.Faker('uuid4')


class ProgramType(DictFactory):
    name = factory.Faker('word')
    logo_image = factory.LazyFunction(generate_sized_stdimage)
