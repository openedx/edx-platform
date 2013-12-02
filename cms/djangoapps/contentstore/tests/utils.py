'''
Utilities for contentstore tests
'''

import json

from student.models import Registration
from django.contrib.auth.models import User
from django.test.client import Client
from django.test.utils import override_settings

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from contentstore.tests.modulestore_config import TEST_MODULESTORE
from xmodule.modulestore.django import loc_mapper


def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)


def user(email):
    """look up a user by email"""
    return User.objects.get(email=email)


def registration(email):
    """look up registration object by email"""
    return Registration.objects.get(user__email=email)


class AjaxEnabledTestClient(Client):
    """
    Convenience class to make testing easier.
    """
    def ajax_post(self, path, data=None, content_type="application/json", **kwargs):
        """
        Convenience method for client post which serializes the data into json and sets the accept type
        to json
        """
        if not isinstance(data, basestring):
            data = json.dumps(data or {})
        kwargs.setdefault("HTTP_X_REQUESTED_WITH", "XMLHttpRequest")
        kwargs.setdefault("HTTP_ACCEPT", "application/json")
        return self.post(path=path, data=data, content_type=content_type, **kwargs)

    def get_html(self, path, data=None, follow=False, **extra):
        """
        Convenience method for client.get which sets the accept type to html
        """
        return self.get(path, data or {}, follow, HTTP_ACCEPT="text/html", **extra)

    def get_json(self, path, data=None, follow=False, **extra):
        """
        Convenience method for client.get which sets the accept type to json
        """
        return self.get(path, data or {}, follow, HTTP_ACCEPT="application/json", **extra)

@override_settings(MODULESTORE=TEST_MODULESTORE)
class CourseTestCase(ModuleStoreTestCase):
    def setUp(self):
        """
        These tests need a user in the DB so that the django Test Client
        can log them in.
        They inherit from the ModuleStoreTestCase class so that the mongodb collection
        will be cleared out before each test case execution and deleted
        afterwards.
        """
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'

        # Create the use so we can log them in.
        self.user = User.objects.create_user(uname, email, password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        self.user.is_active = True
        # Staff has access to view all courses
        self.user.is_staff = True
        self.user.save()

        self.client = AjaxEnabledTestClient()
        self.client.login(username=uname, password=password)

        self.course = CourseFactory.create(
            org='edX',
            number='999',
            display_name='Robot Super Course',
        )
        self.course_location = self.course.location
        self.course_locator = loc_mapper().translate_location(
            self.course.location.course_id, self.course.location, False, True
        )

    def createNonStaffAuthedUserClient(self):
        """
        Create a non-staff user, log them in, and return the client, user to use for testing.
        """
        uname = 'teststudent'
        password = 'foo'
        nonstaff = User.objects.create_user(uname, 'test+student@edx.org', password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        nonstaff.is_active = True
        nonstaff.is_staff = False
        nonstaff.save()

        client = Client()
        client.login(username=uname, password=password)
        return client, nonstaff

    def populateCourse(self):
        """
        Add 2 chapters, 4 sections, 8 verticals, 16 problems to self.course (branching 2)
        """
        def descend(parent, stack):
            xblock_type = stack.pop(0)
            for _ in range(2):
                child = ItemFactory.create(category=xblock_type, parent_location=parent.location)
                if stack:
                    descend(child, stack)

        descend(self.course, ['chapter', 'sequential', 'vertical', 'problem'])
