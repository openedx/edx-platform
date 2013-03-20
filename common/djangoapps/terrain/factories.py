'''
Factories are defined in other modules and absorbed here into the
lettuce world so that they can be used by both unit tests
and integration / BDD tests.

TODO: move the course and item factories out of student and into
xmodule/modulestore
'''
import student.tests.factories as sf
from lettuce import world


@world.absorb
class UserFactory(sf.UserFactory):
    """
    User account for lms / cms
    """
    pass


@world.absorb
class UserProfileFactory(sf.UserProfileFactory):
    """
    Demographics etc for the User
    """
    pass


@world.absorb
class RegistrationFactory(sf.RegistrationFactory):
    """
    Activation key for registering the user account
    """
    pass


@world.absorb
class GroupFactory(sf.GroupFactory):
    """
    Groups for user permissions for courses
    """
    pass


@world.absorb
class CourseEnrollmentAllowedFactory(sf.CourseEnrollmentAllowed):
    """
    Users allowed to enroll in the course outside of the usual window
    """
    pass


@world.absorb
class CourseFactory(sf.CourseFactory):
    """
    Courseware courses
    """
    pass


@world.absorb
class ItemFactory(sf.ItemFactory):
    """
    Everything included inside a course
    """
    pass
