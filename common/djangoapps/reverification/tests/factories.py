"""
verify_student factories
"""
from reverification.models import MidcourseReverificationWindow
from factory.django import DjangoModelFactory
import pytz
from datetime import timedelta, datetime
from opaque_keys.edx.locations import SlashSeparatedCourseKey


# Factories are self documenting
# pylint: disable=missing-docstring
class MidcourseReverificationWindowFactory(DjangoModelFactory):
    """ Creates a generic MidcourseReverificationWindow. """
    FACTORY_FOR = MidcourseReverificationWindow

    course_id = SlashSeparatedCourseKey.from_deprecated_string(u'MITx/999/Robot_Super_Course')
    # By default this factory creates a window that is currently open
    start_date = datetime.now(pytz.UTC) - timedelta(days=100)
    end_date = datetime.now(pytz.UTC) + timedelta(days=100)
