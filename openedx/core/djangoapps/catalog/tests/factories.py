"""Factories for generating fake catalog data."""
# pylint: disable=missing-docstring, invalid-name
from functools import partial

import factory
from faker import Faker


fake = Faker()


def generate_instances(factory_class, count=3):
    """
    Use this to populate fields with values derived from other factories. If
    the array is used directly, the same value will be used repeatedly.
    """
    return factory_class.create_batch(count)


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


class DictFactoryBase(factory.Factory):
    class Meta(object):
        model = dict


class ImageFactoryBase(DictFactoryBase):
    height = factory.Faker('random_int')
    width = factory.Faker('random_int')


class ImageFactory(ImageFactoryBase):
    """
    For constructing dicts mirroring the catalog's serialized representation of ImageFields.

    See https://github.com/edx/course-discovery/blob/master/course_discovery/apps/api/fields.py.
    """
    description = factory.Faker('sentence')
    src = factory.Faker('image_url')


class StdImageFactory(ImageFactoryBase):
    """
    For constructing dicts mirroring the catalog's serialized representation of StdImageFields.

    See https://github.com/edx/course-discovery/blob/master/course_discovery/apps/api/fields.py.
    """
    url = factory.Faker('image_url')


def generate_sized_stdimage():
    return {
        size: StdImageFactory() for size in ['large', 'medium', 'small', 'x-small']
    }


class OrganizationFactory(DictFactoryBase):
    key = factory.Faker('word')
    name = factory.Faker('company')
    uuid = factory.Faker('uuid4')


class SeatFactory(DictFactoryBase):
    type = factory.Faker('word')
    price = factory.Faker('random_int')
    currency = 'USD'


class CourseRunFactory(DictFactoryBase):
    end = factory.LazyFunction(generate_zulu_datetime)
    enrollment_end = factory.LazyFunction(generate_zulu_datetime)
    enrollment_start = factory.LazyFunction(generate_zulu_datetime)
    image = ImageFactory()
    key = factory.LazyFunction(generate_course_run_key)
    marketing_url = factory.Faker('url')
    eligible_for_financial_aid = True
    seats = factory.LazyFunction(partial(generate_instances, SeatFactory))
    pacing_type = 'self_paced'
    short_description = factory.Faker('sentence')
    start = factory.LazyFunction(generate_zulu_datetime)
    title = factory.Faker('catch_phrase')
    type = 'verified'
    uuid = factory.Faker('uuid4')


class CourseFactory(DictFactoryBase):
    course_runs = factory.LazyFunction(partial(generate_instances, CourseRunFactory))
    image = ImageFactory()
    key = factory.LazyFunction(generate_course_key)
    owners = factory.LazyFunction(partial(generate_instances, OrganizationFactory, count=1))
    title = factory.Faker('catch_phrase')
    uuid = factory.Faker('uuid4')


class ProgramFactory(DictFactoryBase):
    authoring_organizations = factory.LazyFunction(partial(generate_instances, OrganizationFactory, count=1))
    banner_image = factory.LazyFunction(generate_sized_stdimage)
    card_image_url = factory.Faker('image_url')
    courses = factory.LazyFunction(partial(generate_instances, CourseFactory))
    marketing_slug = factory.Faker('slug')
    marketing_url = factory.Faker('url')
    status = 'active'
    subtitle = factory.Faker('sentence')
    title = factory.Faker('catch_phrase')
    type = factory.Faker('word')
    uuid = factory.Faker('uuid4')


class ProgramTypeFactory(DictFactoryBase):
    name = factory.Faker('word')
    logo_image = factory.LazyFunction(generate_sized_stdimage)
