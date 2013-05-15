#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from .factories import *
from django.conf import settings
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from student.models import CourseEnrollment
from xmodule.modulestore.django import _MODULESTORES, modulestore
from xmodule.templates import update_templates
from bs4 import BeautifulSoup
import os.path
from urllib import quote_plus
from lettuce.django import django_url


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
def save_the_course_content(path='/tmp'):
    html = world.browser.html.encode('ascii', 'ignore')
    soup = BeautifulSoup(html)

    # get rid of the header, we only want to compare the body
    soup.head.decompose()

    # for now, remove the data-id attributes, because they are
    # causing mismatches between cms-master and master
    for item in soup.find_all(attrs={'data-id': re.compile('.*')}):
        del item['data-id']

    # we also need to remove them from unrendered problems,
    # where they are contained in the text of divs instead of
    # in attributes of tags
    # Be careful of whether or not it was the last attribute
    # and needs a trailing space
    for item in soup.find_all(text=re.compile(' data-id=".*?" ')):
        s = unicode(item.string)
        item.string.replace_with(re.sub(' data-id=".*?" ', ' ', s))

    for item in soup.find_all(text=re.compile(' data-id=".*?"')):
        s = unicode(item.string)
        item.string.replace_with(re.sub(' data-id=".*?"', ' ', s))

    # prettify the html so it will compare better, with
    # each HTML tag on its own line
    output = soup.prettify()

    # use string slicing to grab everything after 'courseware/' in the URL
    u = world.browser.url
    section_url = u[u.find('courseware/') + 11:]


    if not os.path.exists(path):
        os.makedirs(path)

    filename = '%s.html' % (quote_plus(section_url))
    f = open('%s/%s' % (path, filename), 'w')
    f.write(output)
    f.close


@world.absorb
def clear_courses():
    # Flush and initialize the module store
    # It needs the templates because it creates new records
    # by cloning from the template.
    # Note that if your test module gets in some weird state
    # (though it shouldn't), do this manually
    # from the bash shell to drop it:
    # $ mongo test_xmodule --eval "db.dropDatabase()"
    _MODULESTORES = {}
    modulestore().collection.drop()
    update_templates(modulestore('direct'))
