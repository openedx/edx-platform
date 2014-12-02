from course_modes.models import CourseMode
from factory.django import DjangoModelFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey


# Factories are self documenting
# pylint: disable=missing-docstring
class CourseModeFactory(DjangoModelFactory):
    FACTORY_FOR = CourseMode

    course_id = SlashSeparatedCourseKey('MITx', '999', 'Robot_Super_Course')
    mode_slug = 'audit'
    mode_display_name = 'audit course'
    min_price = 0
    currency = 'usd'
    expiration_datetime = None
    suggested_prices = ''
