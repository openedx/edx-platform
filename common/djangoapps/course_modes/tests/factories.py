from course_modes.models import CourseMode
from factory.django import DjangoModelFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey


# Factories don't have __init__ methods, and are self documenting
# pylint: disable=W0232
class CourseModeFactory(DjangoModelFactory):
    FACTORY_FOR = CourseMode

    course_id = SlashSeparatedCourseKey('MITx', '999', 'Robot_Super_Course')
    mode_slug = 'audit'
    mode_display_name = 'audit course'
    min_price = 0
    currency = 'usd'
    expiration_datetime = None
    suggested_prices = ''
