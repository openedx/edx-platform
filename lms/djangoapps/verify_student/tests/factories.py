"""
verify_student factories
"""
from verify_student.models import MidcourseReverificationWindow
from factory.django import DjangoModelFactory
import pytz
from datetime import timedelta, datetime


# Factories don't have __init__ methods, and are self documenting
# pylint: disable=W0232
class MidcourseReverificationWindowFactory(DjangoModelFactory):
    """ Creates a generic MidcourseReverificationWindow. """
    FACTORY_FOR = MidcourseReverificationWindow

    course_id = u'MITx/999/Robot_Super_Course'
    # By default this factory creates a window that is currently open
    start_date = datetime.now(pytz.UTC) - timedelta(days=100)
    end_date = datetime.now(pytz.UTC) + timedelta(days=100)
