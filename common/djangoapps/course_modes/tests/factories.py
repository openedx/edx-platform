from course_modes.models import CourseMode
from factory import DjangoModelFactory

# Factories don't have __init__ methods, and are self documenting
# pylint: disable=W0232
class CourseModeFactory(DjangoModelFactory):
    FACTORY_FOR = CourseMode

    course_id = u'MITx/999/Robot_Super_Course'
    mode_slug = 'audit'
    mode_display_name = 'audit course'
    min_price = 0
    currency = 'usd'
    expiration_datetime = None
