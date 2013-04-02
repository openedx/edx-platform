'''
Factories are defined in other modules and absorbed here into the
lettuce world so that they can be used by both unit tests
and integration / BDD tests.
'''
import student.tests.factories as sf
import xmodule.modulestore.tests.factories as xf
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
class CourseFactory(xf.CourseFactory):
    """
    Courseware courses
    """
    pass


@world.absorb
class ItemFactory(xf.ItemFactory):
    """
    Everything included inside a course
    """
    pass
