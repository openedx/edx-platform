# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

import urllib
from lettuce import world
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore, clear_existing_modulestores
from xmodule.contentstore.django import _CONTENTSTORE


@world.absorb
def create_user(uname, password):

    # If the user already exists, don't try to create it again
    if len(User.objects.filter(username=uname)) > 0:
        return

    portal_user = world.UserFactory.build(username=uname, email=uname + '@edx.org')
    portal_user.set_password(password)
    portal_user.save()

    registration = world.RegistrationFactory(user=portal_user)
    registration.register(portal_user)
    registration.activate()

    world.UserProfileFactory(user=portal_user)


@world.absorb
def log_in(username='robot', password='test', email='robot@edx.org', name="Robot"):
    """
    Use the auto_auth feature to programmatically log the user in
    """
    url = '/auto_auth'
    params = {'username': username, 'password': password, 'email': email, 'full_name': name}
    url += "?" + urllib.urlencode(params)
    world.visit(url)

    # Save the user info in the world scenario_dict for use in the tests
    user = User.objects.get(username=username)
    world.scenario_dict['USER'] = user


@world.absorb
def register_by_course_key(course_key, username='robot', password='test', is_staff=False):
    create_user(username, password)
    user = User.objects.get(username=username)
    # Note: this flag makes the user global staff - that is, an edX employee - not a course staff.
    # See courseware.tests.factories for StaffFactory and InstructorFactory.
    if is_staff:
        user.is_staff = True
        user.save()
    CourseEnrollment.enroll(user, course_key)


@world.absorb
def enroll_user(user, course_key):
    # Activate user
    registration = world.RegistrationFactory(user=user)
    registration.register(user)
    registration.activate()
    # Enroll them in the course
    CourseEnrollment.enroll(user, course_key)


@world.absorb
def clear_courses():
    # Flush and initialize the module store
    # Note that if your test module gets in some weird state
    # (though it shouldn't), do this manually
    # from the bash shell to drop it:
    # $ mongo test_xmodule --eval "db.dropDatabase()"
    modulestore()._drop_database()  # pylint: disable=protected-access
    _CONTENTSTORE.clear()
    clear_existing_modulestores()
