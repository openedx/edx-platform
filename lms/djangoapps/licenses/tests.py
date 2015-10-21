"""Tests for License package"""
import logging
import json

from uuid import uuid4
from random import shuffle
from tempfile import NamedTemporaryFile
import factory
from factory.django import DjangoModelFactory

from django.test import TestCase
from django.test.client import Client
from django.core.management import call_command
from django.core.urlresolvers import reverse
from nose.tools import assert_true  # pylint: disable=no-name-in-module

from licenses.models import CourseSoftware, UserLicense

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

COURSE_1 = 'edX/toy/2012_Fall'

SOFTWARE_1 = 'matlab'
SOFTWARE_2 = 'stata'

SERIAL_1 = '123456abcde'

log = logging.getLogger(__name__)


class CourseSoftwareFactory(DjangoModelFactory):
    '''Factory for generating CourseSoftware objects in database'''
    class Meta(object):
        model = CourseSoftware

    name = SOFTWARE_1
    full_name = SOFTWARE_1
    url = SOFTWARE_1
    course_id = COURSE_1


class UserLicenseFactory(DjangoModelFactory):
    '''
    Factory for generating UserLicense objects in database

    By default, the user assigned is null, indicating that the
    serial number has not yet been assigned.
    '''
    class Meta(object):
        model = UserLicense

    user = None
    software = factory.SubFactory(CourseSoftwareFactory)
    serial = SERIAL_1


class LicenseTestCase(TestCase):
    '''Tests for licenses.views'''
    def setUp(self):
        '''creates a user and logs in'''

        super(LicenseTestCase, self).setUp()
        # self.setup_viewtest_user()
        self.user = UserFactory(username='test',
                                email='test@edx.org', password='test_password')
        self.client = Client()
        assert_true(self.client.login(username='test', password='test_password'))
        self.software = CourseSoftwareFactory()

    def test_get_license(self):
        UserLicenseFactory(user=self.user, software=self.software)
        response = self.client.post(reverse('user_software_license'),
                                    {'software': SOFTWARE_1, 'generate': 'false'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                    HTTP_REFERER='/courses/{0}/some_page'.format(COURSE_1))
        self.assertEqual(200, response.status_code)
        json_returned = json.loads(response.content)
        self.assertFalse('error' in json_returned)
        self.assertTrue('serial' in json_returned)
        self.assertEquals(json_returned['serial'], SERIAL_1)

    def test_get_nonexistent_license(self):
        response = self.client.post(reverse('user_software_license'),
                                    {'software': SOFTWARE_1, 'generate': 'false'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                    HTTP_REFERER='/courses/{0}/some_page'.format(COURSE_1))
        self.assertEqual(200, response.status_code)
        json_returned = json.loads(response.content)
        self.assertFalse('serial' in json_returned)
        self.assertTrue('error' in json_returned)

    def test_create_nonexistent_license(self):
        '''Should not assign a license to an unlicensed user when none are available'''
        response = self.client.post(reverse('user_software_license'),
                                    {'software': SOFTWARE_1, 'generate': 'true'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                    HTTP_REFERER='/courses/{0}/some_page'.format(COURSE_1))
        self.assertEqual(200, response.status_code)
        json_returned = json.loads(response.content)
        self.assertFalse('serial' in json_returned)
        self.assertTrue('error' in json_returned)

    def test_create_license(self):
        '''Should assign a license to an unlicensed user if one is unassigned'''
        # create an unassigned license
        UserLicenseFactory(software=self.software)
        response = self.client.post(reverse('user_software_license'),
                                    {'software': SOFTWARE_1, 'generate': 'true'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                    HTTP_REFERER='/courses/{0}/some_page'.format(COURSE_1))
        self.assertEqual(200, response.status_code)
        json_returned = json.loads(response.content)
        self.assertFalse('error' in json_returned)
        self.assertTrue('serial' in json_returned)
        self.assertEquals(json_returned['serial'], SERIAL_1)

    def test_get_license_from_wrong_course(self):
        response = self.client.post(reverse('user_software_license'),
                                    {'software': SOFTWARE_1, 'generate': 'false'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                    HTTP_REFERER='/courses/{0}/some_page'.format('some/other/course'))
        self.assertEqual(404, response.status_code)

    def test_get_license_from_non_ajax(self):
        response = self.client.post(reverse('user_software_license'),
                                    {'software': SOFTWARE_1, 'generate': 'false'},
                                    HTTP_REFERER='/courses/{0}/some_page'.format(COURSE_1))
        self.assertEqual(404, response.status_code)

    def test_get_license_without_software(self):
        response = self.client.post(reverse('user_software_license'),
                                    {'generate': 'false'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                    HTTP_REFERER='/courses/{0}/some_page'.format(COURSE_1))
        self.assertEqual(404, response.status_code)

    def test_get_license_without_login(self):
        self.client.logout()
        response = self.client.post(reverse('user_software_license'),
                                    {'software': SOFTWARE_1, 'generate': 'false'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                    HTTP_REFERER='/courses/{0}/some_page'.format(COURSE_1))
        # if we're not logged in, we should be referred to the login page
        self.assertEqual(302, response.status_code)


class CommandTest(ModuleStoreTestCase):
    '''Test management command for importing serial numbers'''
    def setUp(self):
        super(CommandTest, self).setUp()

        course = CourseFactory.create()
        self.course_id = course.id

    def test_import_serial_numbers(self):
        size = 20

        log.debug('Adding one set of serials for {0}'.format(SOFTWARE_1))
        with generate_serials_file(size) as temp_file:
            args = [self.course_id.to_deprecated_string(), SOFTWARE_1, temp_file.name]
            call_command('import_serial_numbers', *args)

        log.debug('Adding one set of serials for {0}'.format(SOFTWARE_2))
        with generate_serials_file(size) as temp_file:
            args = [self.course_id.to_deprecated_string(), SOFTWARE_2, temp_file.name]
            call_command('import_serial_numbers', *args)

        log.debug('There should be only 2 course-software entries')
        software_count = CourseSoftware.objects.all().count()
        self.assertEqual(2, software_count)

        log.debug('We added two sets of {0} serials'.format(size))
        licenses_count = UserLicense.objects.all().count()
        self.assertEqual(2 * size, licenses_count)

        log.debug('Adding more serial numbers to {0}'.format(SOFTWARE_1))
        with generate_serials_file(size) as temp_file:
            args = [self.course_id.to_deprecated_string(), SOFTWARE_1, temp_file.name]
            call_command('import_serial_numbers', *args)

        log.debug('There should be still only 2 course-software entries')
        software_count = CourseSoftware.objects.all().count()
        self.assertEqual(2, software_count)

        log.debug(
            "Now we should have 3 sets of %s serials",
            size,
        )
        licenses_count = UserLicense.objects.all().count()
        self.assertEqual(3 * size, licenses_count)

        software = CourseSoftware.objects.get(pk=1)

        lics = UserLicense.objects.filter(software=software)[:size]
        known_serials = list(l.serial for l in lics)
        known_serials.extend(generate_serials(10))

        shuffle(known_serials)

        log.debug('Adding some new and old serials to {0}'.format(SOFTWARE_1))
        with NamedTemporaryFile() as tmpfile:
            tmpfile.write('\n'.join(known_serials))
            tmpfile.flush()
            args = [self.course_id.to_deprecated_string(), SOFTWARE_1, tmpfile.name]
            call_command('import_serial_numbers', *args)

        log.debug('Check if we added only the new ones')
        licenses_count = UserLicense.objects.filter(software=software).count()
        self.assertEqual((2 * size) + 10, licenses_count)


def generate_serials(size=20):
    '''generate a list of serial numbers'''
    return [str(uuid4()) for _ in range(size)]


def generate_serials_file(size=20):
    '''output list of generated serial numbers to a temp file'''
    serials = generate_serials(size)

    temp_file = NamedTemporaryFile()
    temp_file.write('\n'.join(serials))
    temp_file.flush()

    return temp_file
