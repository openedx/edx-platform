# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_group_views.py]
"""
import simplejson as json
import unittest
import uuid

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


TEST_API_KEY = str(uuid.uuid4())


class SecureClient(Client):
    """ Django test client using a "secure" connection. """
    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update({'SERVER_PORT': 443, 'wsgi.url_scheme': 'https'})
        super(SecureClient, self).__init__(*args, **kwargs)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@override_settings(EDX_API_KEY=TEST_API_KEY)
class CoursesApiTests(TestCase):
    """ Test suite for Courses API views """

    def setUp(self):
        self.test_server_prefix = 'https://testserver'
        self.base_courses_uri = '/api/courses'
        self.base_groups_uri = '/api/groups'
        self.test_group_name = 'Alpha Group'

        self.course = CourseFactory.create()
        self.test_data = '<html>{}</html>'.format(str(uuid.uuid4()))

        self.chapter = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            display_name="Overview"
        )

        self.module = ItemFactory.create(
            category="videosequence",
            parent_location=self.chapter.location,
            data=self.test_data,
            display_name="Video_Sequence"
        )

        self.submodule = ItemFactory.create(
            category="video",
            parent_location=self.module.location,
            data=self.test_data,
            display_name="Video_Resources"
        )

        self.test_course_id = self.course.id
        self.test_course_name = self.course.display_name
        self.test_course_number = self.course.number
        self.test_course_org = self.course.org
        self.test_chapter_id = self.chapter.id
        self.test_module_id = self.module.id
        self.test_submodule_id = self.submodule.id
        self.base_modules_uri = '/api/courses/' + self.test_course_id + '/modules'
        self.base_chapters_uri = self.base_modules_uri + '?type=chapter'

        self.client = SecureClient()
        cache.clear()

    def do_get(self, uri):
        """Submit an HTTP GET request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        print "GET: " + uri
        response = self.client.get(uri, headers=headers)
        return response

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        json_data = json.dumps(data)
        print "POST: " + uri
        print json_data
        print ""

        response = self.client.post(uri, headers=headers, content_type='application/json', data=json_data)
        return response

    def do_delete(self, uri):
        """Submit an HTTP DELETE request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.delete(uri, headers=headers)
        return response

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_list_get(self):
        test_uri = self.base_courses_uri
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        matched_course = False
        for course in response.data:
            if matched_course is False and course['id'] == self.test_course_id:
                self.assertEqual(course['name'], self.test_course_name)
                self.assertEqual(course['number'], self.test_course_number)
                self.assertEqual(course['org'], self.test_course_org)
                confirm_uri = self.test_server_prefix + test_uri + '/' + course['id']
                self.assertEqual(course['uri'], confirm_uri)
                matched_course = True
        self.assertTrue(matched_course)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_detail_get(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['id'], self.test_course_id)
        self.assertEqual(response.data['name'], self.test_course_name)
        self.assertEqual(response.data['number'], self.test_course_number)
        self.assertEqual(response.data['org'], self.test_course_org)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertGreater(len(response.data['modules']), 0)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_detail_get_notfound(self):
        test_uri = self.base_courses_uri + '/' + 'p29038cvp9hjwefion'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_chapter_list_get(self):
        test_uri = self.base_chapters_uri
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        matched_chapter = False
        for chapter in response.data:
            if matched_chapter is False and chapter['id'] == self.test_chapter_id:
                self.assertIsNotNone(chapter['uri'])
                self.assertGreater(len(chapter['uri']), 0)
                confirm_uri = self.test_server_prefix + self.base_modules_uri + '/' + chapter['id']
                self.assertEqual(chapter['uri'], confirm_uri)
                matched_chapter = True
        self.assertTrue(matched_chapter)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_chapter_detail_get(self):
        test_uri = self.base_modules_uri + '/' + self.test_chapter_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['id']), 0)
        self.assertEqual(response.data['id'], self.test_chapter_id)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertGreater(len(response.data['modules']), 0)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_modules_list_get(self):
        test_uri = self.base_modules_uri + '/' + self.test_module_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        matched_submodule = False
        for submodule in response.data['modules']:
            if matched_submodule is False and submodule['id'] == self.test_submodule_id:
                self.assertIsNotNone(submodule['uri'])
                self.assertGreater(len(submodule['uri']), 0)
                confirm_uri = self.test_server_prefix + self.base_modules_uri + '/' + submodule['id']
                self.assertEqual(submodule['uri'], confirm_uri)
                matched_submodule = True
        self.assertTrue(matched_submodule)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_modules_detail_get(self):
        test_uri = self.base_modules_uri + '/' + self.test_module_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['id'], self.test_module_id)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertGreater(len(response.data['modules']), 0)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_modules_detail_get_notfound(self):
        test_uri = self.base_modules_uri + '/' + '2p38fp2hjfp9283'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_modules_list_get_filtered_submodules_for_module(self):
        test_uri = self.base_modules_uri + '/' + self.test_module_id + '/submodules?type=video'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        matched_submodule = False
        for submodule in response.data:
            if matched_submodule is False and submodule['id'] == self.test_submodule_id:
                confirm_uri = self.test_server_prefix + self.base_modules_uri + '/' + submodule['id']
                self.assertEqual(submodule['uri'], confirm_uri)
                matched_submodule = True
        self.assertTrue(matched_submodule)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_modules_list_get_notfound(self):
        test_uri = self.base_modules_uri + '/2p38fp2hjfp9283/submodules?type=video'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)


    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_groups_list_post(self):
        data = {'name': self.test_group_name}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']

        test_uri = '{}/{}/groups'.format(self.base_courses_uri, self.test_course_id)
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)

        confirm_uri = self.test_server_prefix + test_uri + '/' + str(group_id)
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['course_id'], str(self.test_course_id))
        self.assertEqual(response.data['group_id'], str(group_id))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_groups_list_post_duplicate(self):
        data = {'name': self.test_group_name}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = '{}/{}/groups'.format(self.base_courses_uri, self.test_course_id)
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_courses_list_post_invalid_resources(self):
        test_uri = self.base_courses_uri + '/1239878976/groups'
        data = {'group_id': "98723896"}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_groups_detail_get(self):
        data = {'name': self.test_group_name}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = '{}/{}/groups'.format(self.base_courses_uri, self.test_course_id)
        data = {'group_id': response.data['id']}
        response = self.do_post(test_uri, data)
        test_uri = response.data['uri']
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['uri'], test_uri)
        self.assertEqual(response.data['course_id'], self.test_course_id)
        self.assertEqual(response.data['group_id'], str(group_id))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_groups_detail_delete(self):
        data = {'name': self.test_group_name}
        response = self.do_post(self.base_groups_uri, data)
        test_uri = '{}/{}/groups'.format(self.base_courses_uri, self.test_course_id)
        data = {'group_id': response.data['id']}
        response = self.do_post(test_uri, data)
        test_uri = response.data['uri']
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)  # Idempotent
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_groups_detail_delete_invalid_course(self):
        test_uri = '{}/123987102/groups/123124'.format(self.base_courses_uri)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_groups_detail_delete_invalid_group(self):
        test_uri = '{}/{}/groups/123124'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_groups_detail_get_undefined(self):
        data = {'name': self.test_group_name}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = '{}/{}/groups/{}'.format(self.base_courses_uri, self.test_course_id, group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
