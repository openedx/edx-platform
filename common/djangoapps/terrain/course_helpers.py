# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world
from .factories import *
from django.conf import settings
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.templates import update_templates
from urllib import quote_plus


@world.absorb
def create_user(uname):

    # If the user already exists, don't try to create it again
    if len(User.objects.filter(username=uname)) > 0:
        return

    portal_user = UserFactory.build(username=uname, email=uname + '@edx.org')
    portal_user.set_password('test')
    portal_user.save()

    registration = world.RegistrationFactory(user=portal_user)
    registration.register(portal_user)
    registration.activate()

    user_profile = world.UserProfileFactory(user=portal_user)


@world.absorb
def log_in(username, password):
    """
    Log the user in programatically.
    This will delete any existing cookies to ensure that the user
    logs in to the correct session.
    """

    # Authenticate the user
    user = authenticate(username=username, password=password)
    assert(user is not None and user.is_active)

    # Send a fake HttpRequest to log the user in
    # We need to process the request using
    # Session middleware and Authentication middleware
    # to ensure that session state can be stored
    request = HttpRequest()
    SessionMiddleware().process_request(request)
    AuthenticationMiddleware().process_request(request)
    login(request, user)

    # Save the session
    request.session.save()

    # Retrieve the sessionid and add it to the browser's cookies
    cookie_dict = {settings.SESSION_COOKIE_NAME: request.session.session_key}
    world.browser.cookies.delete()
    world.browser.cookies.add(cookie_dict)


@world.absorb
def register_by_course_id(course_id, is_staff=False):
    create_user('robot')
    u = User.objects.get(username='robot')
    if is_staff:
        u.is_staff = True
        u.save()
    CourseEnrollment.objects.get_or_create(user=u, course_id=course_id)


@world.absorb
def clear_courses():
    # Flush and initialize the module store
    # It needs the templates because it creates new records
    # by cloning from the template.
    # Note that if your test module gets in some weird state
    # (though it shouldn't), do this manually
    # from the bash shell to drop it:
    # $ mongo test_xmodule --eval "db.dropDatabase()"
    modulestore().collection.drop()
    update_templates(modulestore('direct'))
    contentstore().fs_files.drop()
