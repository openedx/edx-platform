from student.tests.factories import (UserFactory, UserProfileFactory,
                                    RegistrationFactory, GroupFactory, 
                                    CourseEnrollmentAllowed, CourseEnrollment,
                                    CourseFactory, ItemFactory)
from lettuce import world


@world.absorb
class UserFactory(UserFactory):
    """
    User account for lms / cms
    """ 
    pass


@world.absorb
class UserProfileFactory(UserProfileFactory):
    """
    Demographics etc for the User
    """ 
    pass


@world.absorb
class RegistrationFactory(RegistrationFactory):
    """
    Activation key for registering the user account
    """ 
    pass


@world.absorb
class GroupFactory(GroupFactory):
    """
    Groups for user permissions for courses
    """ 
    pass


@world.absorb
class CourseEnrollmentFactory(CourseEnrollment):
    """
    Courses that the user is enrolled in
    """ 
    pass


@world.absorb
class CourseEnrollmentAllowedFactory(CourseEnrollmentAllowed):
    """
    Users allowed to enroll in the course outside of the usual window
    """ 
    pass


@world.absorb
class CourseFactory(CourseFactory):
    """
    Courseware courses
    """ 
    pass
    

@world.absorb
class ItemFactory(ItemFactory):
    """
    Everything included inside a course
    """ 
    pass
