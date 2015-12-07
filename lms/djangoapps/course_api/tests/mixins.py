"""
Common mixins for Course API Tests
"""

from datetime import datetime

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import ToyCourseFactory


TEST_PASSWORD = u'edx'


class CourseApiFactoryMixin(object):
    """
    Mixin to allow creation of test courses and users.
    """

    @staticmethod
    def create_course(**kwargs):
        """
        Create a course for use in test cases
        """

        return ToyCourseFactory.create(
            end=datetime(2015, 9, 19, 18, 0, 0),
            enrollment_start=datetime(2015, 6, 15, 0, 0, 0),
            enrollment_end=datetime(2015, 7, 15, 0, 0, 0),
            **kwargs
        )

    @staticmethod
    def create_user(username, is_staff):
        """
        Create a user as identified by username, email, password and is_staff.
        """
        return UserFactory(
            username=username,
            email=u'{}@example.com'.format(username),
            password=TEST_PASSWORD,
            is_staff=is_staff
        )
