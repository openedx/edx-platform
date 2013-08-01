'''
Test for lms courseware app
'''
import random

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

import xmodule.modulestore.django
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml import XMLModuleStore

from helpers import LoginEnrollmentTestCase
from modulestore_config import TEST_DATA_DIR, \
    TEST_DATA_XML_MODULESTORE, \
    TEST_DATA_MONGO_MODULESTORE, \
    TEST_DATA_DRAFT_MONGO_MODULESTORE
import xmodule


class ActivateLoginTest(LoginEnrollmentTestCase):
    """
    Test logging in and logging out.
    """
    def setUp(self):
        self.setup_user()

    def test_activate_login(self):
        """
        Test login -- the setup function does all the work.
        """
        pass

    def test_logout(self):
        """
        Test logout -- setup function does login.
        """
        self.logout()


class PageLoaderTestCase(LoginEnrollmentTestCase):
    """
    Base class that adds a function to load all pages in a modulestore.
    """

    def check_random_page_loads(self, module_store):
        """
        Choose a page in the course randomly, and assert that it loads.
        """
        # enroll in the course before trying to access pages
        courses = module_store.get_courses()
        self.assertEqual(len(courses), 1)
        course = courses[0]
        self.enroll(course, True)
        course_id = course.id

        # Search for items in the course
        # None is treated as a wildcard
        course_loc = course.location
        location_query = Location(course_loc.tag, course_loc.org,
                                  course_loc.course, None, None, None)

        items = module_store.get_items(location_query)

        if len(items) < 1:
            self.fail('Could not retrieve any items from course')
        else:
            descriptor = random.choice(items)

        # We have ancillary course information now as modules
        # and we can't simply use 'jump_to' to view them
        if descriptor.location.category == 'about':
            self._assert_loads('about_course',
                               {'course_id': course_id},
                               descriptor)

        elif descriptor.location.category == 'static_tab':
            kwargs = {'course_id': course_id,
                      'tab_slug': descriptor.location.name}
            self._assert_loads('static_tab', kwargs, descriptor)

        elif descriptor.location.category == 'course_info':
            self._assert_loads('info', {'course_id': course_id},
                               descriptor)

        elif descriptor.location.category == 'custom_tag_template':
            pass

        else:

            kwargs = {'course_id': course_id,
                      'location': descriptor.location.url()}

            self._assert_loads('jump_to', kwargs, descriptor,
                               expect_redirect=True,
                               check_content=True)

    def _assert_loads(self, django_url, kwargs, descriptor,
                      expect_redirect=False,
                      check_content=False):
        """
        Assert that the url loads correctly.
        If expect_redirect, then also check that we were redirected.
        If check_content, then check that we don't get
        an error message about unavailable modules.
        """

        url = reverse(django_url, kwargs=kwargs)
        response = self.client.get(url, follow=True)

        if response.status_code != 200:
            self.fail('Status %d for page %s' %
                      (response.status_code, descriptor.location.url()))

        if expect_redirect:
            self.assertEqual(response.redirect_chain[0][1], 302)

        if check_content:
            self.assertNotContains(response, "this module is temporarily unavailable")
            self.assertNotIsInstance(descriptor, ErrorDescriptor)


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestCoursesLoadTestCase_XmlModulestore(PageLoaderTestCase):
    """
    Check that all pages in test courses load properly from XML.
    """

    def setUp(self):
        super(TestCoursesLoadTestCase_XmlModulestore, self).setUp()
        self.setup_user()
        xmodule.modulestore.django._MODULESTORES.clear()

    def test_toy_course_loads(self):
        module_class = 'xmodule.hidden_module.HiddenDescriptor'
        module_store = XMLModuleStore(TEST_DATA_DIR,
                                      default_class=module_class,
                                      course_dirs=['toy'],
                                      load_error_modules=True)

        self.check_random_page_loads(module_store)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestCoursesLoadTestCase_MongoModulestore(PageLoaderTestCase):
    """
    Check that all pages in test courses load properly from Mongo.
    """

    def setUp(self):
        super(TestCoursesLoadTestCase_MongoModulestore, self).setUp()
        self.setup_user()
        xmodule.modulestore.django._MODULESTORES.clear()
        modulestore().collection.drop()

    def test_toy_course_loads(self):
        module_store = modulestore()
        import_from_xml(module_store, TEST_DATA_DIR, ['toy'])
        self.check_random_page_loads(module_store)

    def test_toy_textbooks_loads(self):
        module_store = modulestore()
        import_from_xml(module_store, TEST_DATA_DIR, ['toy'])

        course = module_store.get_item(Location(['i4x', 'edX', 'toy', 'course', '2012_Fall', None]))

        self.assertGreater(len(course.textbooks), 0)

@override_settings(MODULESTORE=TEST_DATA_DRAFT_MONGO_MODULESTORE)
class TestDraftModuleStore(TestCase):
    def test_get_items_with_course_items(self):
        store = modulestore()

        # fix was to allow get_items() to take the course_id parameter
        store.get_items(Location(None, None, 'vertical', None, None),
                        course_id='abc', depth=0)

        # test success is just getting through the above statement.
        # The bug was that 'course_id' argument was
        # not allowed to be passed in (i.e. was throwing exception)
