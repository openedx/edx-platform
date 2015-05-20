""" Tests for credit course tasks """

from datetime import datetime

from openedx.core.djangoapps.credit.api import get_credit_requirements
from openedx.core.djangoapps.credit.models import CreditCourse
from openedx.core.djangoapps.credit.signals import listen_for_course_publish
from xmodule.modulestore.django import SignalHandler
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestTaskExecution(ModuleStoreTestCase):
    """
    Set of tests to ensure that the task code will do the right thing when
    executed directly. The test course gets created without the listeners
    being present, which allows us to ensure that when the listener is
    executed, it is done as expected.
    """

    def setUp(self):
        super(TestTaskExecution, self).setUp()

        SignalHandler.course_published.disconnect(listen_for_course_publish)
        self.course = CourseFactory.create(start=datetime(2015, 3, 1))

    def test_task_adding_requirements_invalid_course(self):
        """
        Make sure that the receiver correctly fires off the task when
        invoked by signal
        """
        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)
        listen_for_course_publish(self, self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)

    def test_task_adding_requirements(self):
        """
        Make sure that the receiver correctly fires off the task when
        invoked by signal
        """
        self.add_credit_course(self.course.id)
        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 0)
        listen_for_course_publish(self, self.course.id)

        requirements = get_credit_requirements(self.course.id)
        self.assertEqual(len(requirements), 1)

    def add_credit_course(self, course_key):
        """ Add the course as a credit

        Args:
            course_key(CourseKey): identifier for the course

        Returns:
            CreditCourse object added
        """
        credit_course = CreditCourse(course_key=course_key, enabled=True)
        credit_course.save()
        return credit_course
