# pylint: disable=E1103
"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/courses/tests.py]
"""
from datetime import datetime
import json
import uuid
import mock
from random import randint
from urllib import urlencode
from freezegun import freeze_time
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client
from django.test.utils import override_settings

from capa.tests.response_xml_factory import StringResponseXMLFactory
from courseware import module_render
from courseware.tests.factories import StudentModuleFactory
from courseware.model_data import FieldDataCache
from django_comment_common.models import Role, FORUM_ROLE_MODERATOR
from instructor.access import allow_access
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from .content import TEST_COURSE_OVERVIEW_CONTENT, TEST_COURSE_UPDATES_CONTENT, TEST_COURSE_UPDATES_CONTENT_LEGACY
from .content import TEST_STATIC_TAB1_CONTENT, TEST_STATIC_TAB2_CONTENT

TEST_API_KEY = str(uuid.uuid4())
USER_COUNT = 6
SAMPLE_GRADE_DATA_COUNT = 4


class SecureClient(Client):
    """ Django test client using a "secure" connection. """
    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update({'SERVER_PORT': 443, 'wsgi.url_scheme': 'https'})
        super(SecureClient, self).__init__(*args, **kwargs)

def _fake_get_get_course_social_stats(course_id):
    return {
        '1': {'foo':'bar'},
        '2': {'one': 'two'}
    }


def _fake_get_course_thread_stats(course_id):
    return {
        'num_threads': 5,
        'num_active_threads': 3
    }


@mock.patch("api_manager.courses.views.get_course_social_stats", _fake_get_get_course_social_stats)
@mock.patch("api_manager.courses.views.get_course_thread_stats", _fake_get_course_thread_stats)
@override_settings(EDX_API_KEY=TEST_API_KEY)
@mock.patch.dict("django.conf.settings.FEATURES", {'ENFORCE_PASSWORD_POLICY': False,
                                                   'ADVANCED_SECURITY': False,
                                                   'PREVENT_CONCURRENT_LOGINS': False
                                                   })
class CoursesApiTests(ModuleStoreTestCase):
    """ Test suite for Courses API views """

    def get_module_for_user(self, user, course, problem):
        """Helper function to get useful module at self.location in self.course_id for user"""
        mock_request = mock.MagicMock()
        mock_request.user = user
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, user, course, depth=2)
        module = module_render.get_module(  # pylint: disable=protected-access
            user,
            mock_request,
            problem.location,
            field_data_cache,
            course.id
        )
        return module


    def setUp(self):
        self.test_server_prefix = 'https://testserver'
        self.base_courses_uri = '/api/server/courses'
        self.base_groups_uri = '/api/server/groups'
        self.base_users_uri = '/api/server/users'
        self.base_organizations_uri = '/api/server/organizations/'
        self.base_projects_uri = '/api/server/projects/'
        self.base_workgroups_uri = '/api/server/workgroups/'
        self.test_group_name = 'Alpha Group'
        self.attempts = 3

        self.course = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16)
        )
        self.test_data = '<html>{}</html>'.format(str(uuid.uuid4()))

        self.chapter = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )

        self.course_project = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            display_name="Group Project"
        )

        self.course_project2 = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            display_name="Group Project2"
        )

        self.course_content = ItemFactory.create(
            category="videosequence",
            parent_location=self.chapter.location,
            data=self.test_data,
            display_name="Video_Sequence"
        )

        self.content_child = ItemFactory.create(
            category="video",
            parent_location=self.course_content.location,
            data=self.test_data,
            display_name="Video_Resources"
        )

        self.overview = ItemFactory.create(
            category="about",
            parent_location=self.course.location,
            data=TEST_COURSE_OVERVIEW_CONTENT,
            display_name="overview"
        )

        self.updates = ItemFactory.create(
            category="course_info",
            parent_location=self.course.location,
            data=TEST_COURSE_UPDATES_CONTENT,
            display_name="updates"
        )

        self.static_tab1 = ItemFactory.create(
            category="static_tab",
            parent_location=self.course.location,
            data=TEST_STATIC_TAB1_CONTENT,
            display_name="syllabus"
        )

        self.static_tab2 = ItemFactory.create(
            category="static_tab",
            parent_location=self.course.location,
            data=TEST_STATIC_TAB2_CONTENT,
            display_name="readings"
        )

        self.sub_section = ItemFactory.create(
            parent_location=self.chapter.location,
            category="sequential",
            display_name=u"test subsection",
        )

        self.unit = ItemFactory.create(
            parent_location=self.sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test unit",
        )

        self.dash_unit = ItemFactory.create(
            parent_location=self.sub_section.location,
            category="vertical-with-dash",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test unit 2",
        )

        self.empty_course = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16),
            org="MTD"
        )

        self.users = [UserFactory.create(username="testuser" + str(__), profile='test') for __ in xrange(USER_COUNT)]

        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)
            user_profile = user.profile
            user_profile.avatar_url = 'http://example.com/{}.png'.format(user.id)
            user_profile.title = 'Software Engineer {}'.format(user.id)
            user_profile.city = 'Cambridge'
            user_profile.save()

        for i in xrange(SAMPLE_GRADE_DATA_COUNT - 1):
            section = 'Midterm Exam'
            if i % 2 is 0:
                section = "Final Exam"
            self.item = ItemFactory.create(
                parent_location=self.chapter.location,
                category='problem',
                data=StringResponseXMLFactory().build_xml(answer='bar'),
                display_name='Problem {}'.format(i),
                metadata={'rerandomize': 'always', 'graded': True, 'format': section}
            )

            for j, user in enumerate(self.users):
                points_scored = (j + 1) * 20
                points_possible = 100
                module = self.get_module_for_user(user, self.course, self.item)
                grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
                module.system.publish(module, 'grade', grade_dict)

                StudentModuleFactory.create(
                    course_id=self.course.id,
                    module_type='sequential',
                    module_state_key=self.item.location,
                )

        self.test_course_id = unicode(self.course.id)
        self.test_bogus_course_id = 'foo/bar/baz'
        self.test_course_name = self.course.display_name
        self.test_course_number = self.course.number
        self.test_course_org = self.course.org
        self.test_chapter_id = unicode(self.chapter.scope_ids.usage_id)
        self.test_course_content_id = unicode(self.course_content.scope_ids.usage_id)
        self.test_bogus_content_id = "j5y://foo/bar/baz"
        self.test_content_child_id = unicode(self.content_child.scope_ids.usage_id)
        self.base_course_content_uri = '{}/{}/content'.format(self.base_courses_uri, self.test_course_id)
        self.base_chapters_uri = self.base_course_content_uri + '?type=chapter'

        self.client = SecureClient()
        cache.clear()

        Role.objects.get_or_create(
            name=FORUM_ROLE_MODERATOR,
            course_id=self.course.id)

    def do_get(self, uri):
        """Submit an HTTP GET request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.get(uri, headers=headers)
        return response

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'X-Edx-Api-Key': str(TEST_API_KEY),
            'Content-Type': 'application/json'
        }
        json_data = json.dumps(data)
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

    def _find_item_by_class(self, items, class_name):
        """Helper method to match a single matching item"""
        for item in items:
            if item['class'] == class_name:
                return item
        return None

    def test_courses_list_get(self):
        test_uri = self.base_courses_uri
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['results']), 0)
        self.assertIsNotNone(response.data['count'])
        self.assertIsNotNone(response.data['num_pages'])
        matched_course = False
        for course in response.data['results']:
            if matched_course is False and course['id'] == self.test_course_id:
                self.assertEqual(course['name'], self.test_course_name)
                self.assertEqual(course['number'], self.test_course_number)
                self.assertEqual(course['org'], self.test_course_org)
                confirm_uri = self.test_server_prefix + test_uri + '/' + course['id']
                self.assertEqual(course['uri'], confirm_uri)
                matched_course = True
        self.assertTrue(matched_course)

    def test_courses_list_get_with_filter(self):
        test_uri = self.base_courses_uri
        courses = [self.test_course_id, unicode(self.empty_course.id)]
        params = {'course_id': ','.join(courses).encode('utf-8')}
        response = self.do_get('{}/?{}'.format(test_uri, urlencode(params)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['count'])
        self.assertIsNotNone(response.data['num_pages'])
        courses_in_result = []
        for course in response.data['results']:
            courses_in_result.append(course['id'])
            if course['id'] == self.test_course_id:
                self.assertEqual(course['name'], self.test_course_name)
                self.assertEqual(course['number'], self.test_course_number)
                self.assertEqual(course['org'], self.test_course_org)
                confirm_uri = self.test_server_prefix + test_uri + '/' + course['id']
                self.assertEqual(course['uri'], confirm_uri)
                self.assertIsNotNone(course['course_image_url'])
        self.assertItemsEqual(courses, courses_in_result)


    def test_course_detail_without_date_values(self):
        create_course_with_out_date_values = CourseFactory.create()  # pylint: disable=C0103
        test_uri = self.base_courses_uri + '/' + unicode(create_course_with_out_date_values.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['start'], create_course_with_out_date_values.start)
        self.assertEqual(response.data['end'], create_course_with_out_date_values.end)

    def test_courses_detail_get(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['id'], self.test_course_id)
        self.assertEqual(response.data['name'], self.test_course_name)
        self.assertEqual(datetime.strftime(response.data['start'], '%Y-%m-%d %H:%M:%S'), datetime.strftime(self.course.start, '%Y-%m-%d %H:%M:%S'))
        self.assertEqual(datetime.strftime(response.data['end'], '%Y-%m-%d %H:%M:%S'), datetime.strftime(self.course.end, '%Y-%m-%d %H:%M:%S'))
        self.assertEqual(response.data['number'], self.test_course_number)
        self.assertEqual(response.data['org'], self.test_course_org)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)

    def test_courses_detail_get_with_child_content(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id
        response = self.do_get('{}?depth=100'.format(test_uri))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['id'], self.test_course_id)
        self.assertEqual(response.data['name'], self.test_course_name)
        self.assertEqual(response.data['number'], self.test_course_number)
        self.assertEqual(response.data['org'], self.test_course_org)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertGreater(len(response.data['content']), 0)
        for resource in response.data['resources']:
            response = self.do_get(resource['uri'])
            self.assertEqual(response.status_code, 200)

    def test_courses_detail_get_notfound(self):
        test_uri = self.base_courses_uri + '/' + self.test_bogus_course_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_tree_get(self):
        # query the course tree to quickly get naviation information
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '?depth=2'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['category'], 'course')
        self.assertEqual(response.data['name'], self.course.display_name)
        self.assertEqual(len(response.data['content']), 3)

        chapter = response.data['content'][0]
        self.assertEqual(chapter['category'], 'chapter')
        self.assertEqual(chapter['name'], 'Overview')
        self.assertEqual(len(chapter['children']), 5)

        sequence = chapter['children'][0]
        self.assertEqual(sequence['category'], 'videosequence')
        self.assertEqual(sequence['name'], 'Video_Sequence')
        self.assertNotIn('children', sequence)

    def test_courses_tree_get_root(self):
        # query the course tree to quickly get naviation information
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '?depth=0'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['category'], 'course')
        self.assertEqual(response.data['name'], self.course.display_name)
        self.assertNotIn('content', response.data)

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
                confirm_uri = self.test_server_prefix + self.base_course_content_uri + '/' + chapter['id']
                self.assertEqual(chapter['uri'], confirm_uri)
                matched_chapter = True
        self.assertTrue(matched_chapter)

    def test_chapter_detail_get(self):
        test_uri = self.base_course_content_uri + '/' + self.test_chapter_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['id']), 0)
        self.assertEqual(response.data['id'], self.test_chapter_id)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertGreater(len(response.data['children']), 0)

    def test_course_content_list_get(self):
        test_uri = '{}/{}/children'.format(self.base_course_content_uri, self.test_course_content_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        matched_child = False
        for child in response.data:
            if matched_child is False and child['id'] == self.test_content_child_id:
                self.assertIsNotNone(child['uri'])
                self.assertGreater(len(child['uri']), 0)
                confirm_uri = self.test_server_prefix + self.base_course_content_uri + '/' + child['id']
                self.assertEqual(child['uri'], confirm_uri)
                matched_child = True
        self.assertTrue(matched_child)

    def test_course_content_list_get_invalid_course(self):
        test_uri = '{}/{}/content/{}/children'.format(self.base_courses_uri, self.test_bogus_course_id, unicode(self.course_project.scope_ids.usage_id))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_content_list_get_invalid_content(self):
        test_uri = '{}/{}/children'.format(self.base_course_content_uri, self.test_bogus_content_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_content_detail_get(self):
        test_uri = self.base_course_content_uri + '/' + self.test_course_content_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['id'], self.test_course_content_id)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertGreater(len(response.data['children']), 0)

    def test_course_content_detail_get_with_extra_fields(self):
        test_uri = self.base_course_content_uri + '/' + self.test_course_content_id
        response = self.do_get('{}?include_fields=course_edit_method,edited_by'.format(test_uri))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertIsNotNone(response.data['course_edit_method'])
        self.assertIsNotNone(response.data['edited_by'])

    def test_course_content_detail_get_dashed_id(self):
        test_content_id = unicode(self.dash_unit.scope_ids.usage_id)
        test_uri = self.base_course_content_uri + '/' + test_content_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['id'], test_content_id)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)

    def test_course_content_detail_get_course(self):
        test_uri = self.base_course_content_uri + '/' + self.test_course_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['id'], self.test_course_id)
        confirm_uri = self.test_server_prefix + self.base_courses_uri + '/' + self.test_course_id
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertGreater(len(response.data['content']), 0)

    def test_course_content_detail_get_notfound(self):
        test_uri = self.base_course_content_uri + '/' + self.test_bogus_content_id
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_content_list_get_filtered_children_for_child(self):
        test_uri = self.base_course_content_uri + '/' + self.test_course_content_id + '/children?type=video'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        matched_child = False
        for child in response.data:
            if matched_child is False and child['id'] == self.test_content_child_id:
                confirm_uri = '{}{}/{}'.format(self.test_server_prefix, self.base_course_content_uri, child['id'])
                self.assertEqual(child['uri'], confirm_uri)
                matched_child = True
        self.assertTrue(matched_child)

    def test_course_content_list_get_notfound(self):
        test_uri = '{}{}/children?type=video'.format(self.base_course_content_uri, self.test_bogus_content_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_groups_list_post(self):
        data = {'name': self.test_group_name, 'type': 'test'}
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

    def test_courses_groups_list_get(self):
        test_uri = '{}/{}/groups'.format(self.base_courses_uri, self.test_course_id)
        course_fail_uri = '{}/{}/groups'.format(self.base_courses_uri, 'ed/Open_DemoX/edx_demo_course')
        for i in xrange(2):
            data_dict = {
                'name': 'Alpha Group {}'.format(i), 'type': 'Programming',
            }
            response = self.do_post(self.base_groups_uri, data_dict)
            group_id = response.data['id']
            data = {'group_id': group_id}
            self.assertEqual(response.status_code, 201)
            response = self.do_post(test_uri, data)
            self.assertEqual(response.status_code, 201)

        data_dict['type'] = 'Calculus'
        response = self.do_post(self.base_groups_uri, data_dict)
        group_id = response.data['id']
        data = {'group_id': group_id}
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

        courses_groups_uri = '{}?type={}'.format(test_uri, 'Programming')
        response = self.do_get(courses_groups_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        group_type_uri = '{}?type={}'.format(test_uri, 'Calculus')
        response = self.do_get(group_type_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        error_group_type_uri = '{}?type={}'.format(test_uri, 'error_type')
        response = self.do_get(error_group_type_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        response = self.do_get(course_fail_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_groups_list_post_duplicate(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = '{}/{}/groups'.format(self.base_courses_uri, self.test_course_id)
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)

    def test_courses_groups_list_post_invalid_course(self):
        test_uri = self.base_courses_uri + '/1239/87/8976/groups'
        data = {'group_id': "98723896"}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_courses_groups_list_post_invalid_group(self):
        test_uri = '{}/{}/groups'.format(self.base_courses_uri, self.test_course_id)
        data = {'group_id': "98723896"}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_courses_groups_detail_get(self):
        data = {'name': self.test_group_name, 'type': 'test'}
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

    def test_courses_groups_detail_get_invalid_resources(self):
        test_uri = '{}/{}/groups/123145'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

        test_uri = '{}/{}/groups/123145'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        test_uri = '{}/{}/groups/{}'.format(self.base_courses_uri, self.test_course_id, response.data['id'])
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_groups_detail_delete(self):
        data = {'name': self.test_group_name, 'type': 'test'}
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

    def test_courses_groups_detail_delete_invalid_course(self):
        test_uri = '{}/{}/groups/123124'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_courses_groups_detail_delete_invalid_group(self):
        test_uri = '{}/{}/groups/123124'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_courses_groups_detail_get_undefined(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = '{}/{}/groups/{}'.format(self.base_courses_uri, self.test_course_id, group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_overview_get_unparsed(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/overview'

        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['overview_html'], self.overview.data)
        self.assertIn(self.course.course_image, response.data['course_image_url'])

    def test_courses_overview_get_parsed(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/overview?parse=true'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertIn(self.course.course_image, response.data['course_image_url'])
        sections = response.data['sections']
        self.assertEqual(len(sections), 5)
        self.assertIsNotNone(self._find_item_by_class(sections, 'about'))
        self.assertIsNotNone(self._find_item_by_class(sections, 'prerequisites'))
        self.assertIsNotNone(self._find_item_by_class(sections, 'course-staff'))
        self.assertIsNotNone(self._find_item_by_class(sections, 'faq'))
        self.assertIsNotNone(self._find_item_by_class(sections, 'intro-video'))

        course_staff = self._find_item_by_class(sections, 'course-staff')
        staff = course_staff['articles']
        self.assertEqual(len(staff), 3)
        self.assertEqual(staff[0]['class'], "teacher")
        self.assertEqual(staff[0]['name'], "Staff Member #1")
        self.assertEqual(staff[0]['image_src'], "/images/pl-faculty.png")
        self.assertIn("<p>Biography of instructor/staff member #1</p>", staff[0]['bio'])
        self.assertEqual(staff[1]['class'], "teacher")
        self.assertEqual(staff[1]['name'], "Staff Member #2")
        self.assertEqual(staff[1]['image_src'], "/images/pl-faculty.png")
        self.assertIn("<p>Biography of instructor/staff member #2</p>", staff[1]['bio'])
        self.assertEqual(staff[2]['class'], "author")
        body = staff[2]['body']
        self.assertGreater(len(body), 0)

        about = self._find_item_by_class(sections, 'about')
        self.assertGreater(len(about['body']), 0)
        prerequisites = self._find_item_by_class(sections, 'prerequisites')
        self.assertGreater(len(prerequisites['body']), 0)
        faq = self._find_item_by_class(sections, 'faq')
        self.assertGreater(len(faq['body']), 0)
        invalid_tab = self._find_item_by_class(sections, 'invalid_tab')
        self.assertFalse(invalid_tab)

        intro_video = self._find_item_by_class(sections, 'intro-video')
        self.assertEqual(len(intro_video['attributes']), 1)
        self.assertEqual(intro_video['attributes']['data-videoid'], 'foobar')

    def test_courses_overview_get_invalid_course(self):
        #try a bogus course_id to test failure case
        test_uri = '{}/{}/overview'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_overview_get_invalid_content(self):
        #try a bogus course_id to test failure case
        test_course = CourseFactory.create()
        test_uri = '{}/{}/overview'.format(self.base_courses_uri, unicode(test_course.id))
        ItemFactory.create(
            category="about",
            parent_location=test_course.location,
            data='',
            display_name="overview"
        )
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_updates_get(self):
        # first try raw without any parsing
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/updates'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['content'], self.updates.data)

        # then try parsed
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/updates?parse=True'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

        postings = response.data['postings']
        self.assertEqual(len(postings), 4)
        self.assertEqual(postings[0]['date'], 'April 18, 2014')
        self.assertEqual(postings[0]['content'], 'This does not have a paragraph tag around it')
        self.assertEqual(postings[1]['date'], 'April 17, 2014')
        self.assertEqual(postings[1]['content'], 'Some text before paragraph tag<p>This is inside paragraph tag</p>Some text after tag')
        self.assertEqual(postings[2]['date'], 'April 16, 2014')
        self.assertEqual(postings[2]['content'], 'Some text before paragraph tag<p>This is inside paragraph tag</p>Some text after tag<p>one more</p>')
        self.assertEqual(postings[3]['date'], 'April 15, 2014')
        self.assertEqual(postings[3]['content'], '<p>A perfectly</p><p>formatted piece</p><p>of HTML</p>')

    def test_courses_updates_get_invalid_course(self):
        #try a bogus course_id to test failure case
        test_uri = '{}/{}/updates'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_updates_get_invalid_content(self):
        #try a bogus course_id to test failure case
        test_course = CourseFactory.create()
        ItemFactory.create(
            category="course_info",
            parent_location=test_course.location,
            data='',
            display_name="updates"
        )
        test_uri = '{}/{}/updates'.format(self.base_courses_uri, unicode(test_course.id))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_updates_legacy(self):
        #try a bogus course_id to test failure case
        test_course = CourseFactory.create()
        ItemFactory.create(
            category="course_info",
            parent_location=test_course.location,
            data=TEST_COURSE_UPDATES_CONTENT_LEGACY,
            display_name="updates"
        )
        test_uri = self.base_courses_uri + '/' + unicode(test_course.id) + '/updates'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data['content'], TEST_COURSE_UPDATES_CONTENT_LEGACY)

        # then try parsed
        test_uri = self.base_courses_uri + '/' + unicode(test_course.id) + '/updates?parse=True'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

        postings = response.data['postings']
        self.assertEqual(len(postings), 4)
        self.assertEqual(postings[0]['date'], 'April 18, 2014')
        self.assertEqual(postings[0]['content'], 'This is some legacy content')
        self.assertEqual(postings[1]['date'], 'April 17, 2014')
        self.assertEqual(postings[1]['content'], 'Some text before paragraph tag<p>This is inside paragraph tag</p>Some text after tag')
        self.assertEqual(postings[2]['date'], 'April 16, 2014')
        self.assertEqual(postings[2]['content'], 'Some text before paragraph tag<p>This is inside paragraph tag</p>Some text after tag<p>one more</p>')
        self.assertEqual(postings[3]['date'], 'April 15, 2014')
        self.assertEqual(postings[3]['content'], '<p>A perfectly</p><p>formatted piece</p><p>of HTML</p>')

    def test_static_tab_list_get(self):
        test_uri = '{}/{}/static_tabs'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

        tabs = response.data['tabs']
        self.assertEqual(len(tabs), 2)
        self.assertEqual(tabs[0]['name'], u'syllabus')
        self.assertEqual(tabs[0]['id'], u'syllabus')
        self.assertEqual(tabs[1]['name'], u'readings')
        self.assertEqual(tabs[1]['id'], u'readings')

        # now try when we get the details on the tabs
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/static_tabs?detail=true'
        response = self.do_get(test_uri)

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

        tabs = response.data['tabs']
        self.assertEqual(tabs[0]['name'], u'syllabus')
        self.assertEqual(tabs[0]['id'], u'syllabus')
        self.assertEqual(tabs[0]['content'], self.static_tab1.data)
        self.assertEqual(tabs[1]['name'], u'readings')
        self.assertEqual(tabs[1]['id'], u'readings')
        self.assertEqual(tabs[1]['content'], self.static_tab2.data)

    def test_static_tab_list_get_invalid_course(self):
        #try a bogus course_id to test failure case
        test_uri = self.base_courses_uri + '/' + self.test_bogus_course_id + '/static_tabs'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_static_tab_detail_get(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/static_tabs/syllabus'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        tab = response.data
        self.assertEqual(tab['name'], u'syllabus')
        self.assertEqual(tab['id'], u'syllabus')
        self.assertEqual(tab['content'], self.static_tab1.data)

        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/static_tabs/readings'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        tab = response.data
        self.assertEqual(tab['name'], u'readings')
        self.assertEqual(tab['id'], u'readings')
        self.assertEqual(tab['content'], self.static_tab2.data)

    def test_static_tab_detail_get_invalid_course(self):
        # try a bogus courseId
        test_uri = self.base_courses_uri + '/' + self.test_bogus_course_id + '/static_tabs/syllabus'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_static_tab_detail_get_invalid_item(self):
        # try a not found item
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/static_tabs/bogus'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_users_list_get_no_students(self):
        course = CourseFactory.create(display_name="TEST COURSE", org='TESTORG')
        test_uri = self.base_courses_uri + '/' + unicode(course.id) + '/users'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

        # assert that there is no enrolled students
        enrollments = response.data['enrollments']
        self.assertEqual(len(enrollments), 0)
        self.assertNotIn('pending_enrollments', response.data)

    def test_courses_users_list_invalid_course(self):
        test_uri = self.base_courses_uri + '/' + self.test_bogus_course_id + '/users'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_users_list_post_nonexisting_user_deny(self):
        # enroll a non-existing student
        # first, don't allow non-existing
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
        post_data = {
            'email': 'test+pending@tester.com',
            'allow_pending': False,
        }
        response = self.do_post(test_uri, post_data)
        self.assertEqual(response.status_code, 400)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

    def test_courses_users_list_post_nonexisting_user_allow(self):
        course = CourseFactory.create(display_name="TEST COURSE", org='TESTORG2')
        test_uri = self.base_courses_uri + '/' + unicode(course.id) + '/users'
        post_data = {}
        post_data['email'] = 'test+pending@tester.com'
        post_data['allow_pending'] = True
        response = self.do_post(test_uri, post_data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['enrollments']), 0)

    def test_courses_users_list_post_existing_user(self):
        # create a new user (note, this calls into the /users/ subsystem)
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
        test_user_uri = self.base_users_uri
        local_username = "some_test_user" + str(randint(11, 99))
        local_email = "test+notpending@tester.com"
        data = {
            'email': local_email,
            'username': local_username,
            'password': 'fooabr',
            'first_name': 'Joe',
            'last_name': 'Brown'
        }
        response = self.do_post(test_user_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        created_user_id = response.data['id']

        # now enroll this user in the course
        post_data = {}
        post_data['user_id'] = created_user_id
        response = self.do_post(test_uri, post_data)
        self.assertEqual(response.status_code, 201)

    def test_courses_users_list_post_invalid_course(self):
        test_uri = self.base_courses_uri + '/' + self.test_bogus_course_id + '/users'
        post_data = {}
        post_data['email'] = 'test+pending@tester.com'
        post_data['allow_pending'] = True
        response = self.do_post(test_uri, post_data)
        self.assertEqual(response.status_code, 404)

    def test_courses_users_list_post_invalid_user(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
        post_data = {}
        post_data['user_id'] = '123123124'
        post_data['allow_pending'] = True
        response = self.do_post(test_uri, post_data)
        self.assertEqual(response.status_code, 404)

    def test_courses_users_list_post_invalid_payload(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
        post_data = {}
        response = self.do_post(test_uri, post_data)
        self.assertEqual(response.status_code, 400)

    def test_courses_users_list_get(self):
        # create a new user (note, this calls into the /users/ subsystem)
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
        test_user_uri = self.base_users_uri
        local_username = "some_test_user" + str(randint(11, 99))
        local_email = "test+notpending@tester.com"
        data = {
            'email': local_email,
            'username': local_username,
            'password': 'fooabr',
            'first_name': 'Joe',
            'last_name': 'Brown'
        }
        response = self.do_post(test_user_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        created_user_id = response.data['id']
        post_data = {}
        post_data['user_id'] = created_user_id
        response = self.do_post(test_uri, post_data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)

    def test_courses_users_list_get_filter_by_orgs(self):
        # create 5 users
        users = []
        for i in xrange(1, 6):
            data = {
                'email': 'test{}@example.com'.format(i),
                'username': 'test_user{}'.format(i),
                'password': 'test_pass',
                'first_name': 'John{}'.format(i),
                'last_name': 'Doe{}'.format(i)
            }
            response = self.do_post(self.base_users_uri, data)
            self.assertEqual(response.status_code, 201)
            users.append(response.data['id'])

        # create 3 organizations each one having one user
        org_ids = []
        for i in xrange(1, 4):
            data = {
                'name': '{} {}'.format('Test Organization', i),
                'display_name': '{} {}'.format('Test Org Display Name', i),
                'users': [users[i]]
            }
            response = self.do_post(self.base_organizations_uri, data)
            self.assertEqual(response.status_code, 201)
            self.assertGreater(response.data['id'], 0)
            org_ids.append(response.data['id'])

        # enroll all users in course
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
        for user in users:
            data = {'user_id': user}
            response = self.do_post(test_uri, data)
            self.assertEqual(response.status_code, 201)

        # retrieve all users enrolled in the course
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['enrollments']), 5)

        # retrieve users by organization
        response = self.do_get('{}?organizations={}'.format(test_uri, org_ids[0]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['enrollments']), 1)

        # retrieve all users enrolled in the course
        response = self.do_get('{}?organizations={},{},{}'.format(test_uri, org_ids[0], org_ids[1], org_ids[2]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['enrollments']), 3)

    def test_courses_users_list_get_filter_by_groups(self):
        # create 2 groups
        group_ids = []
        for i in xrange(1, 3):
            data = {'name': '{} {}'.format(self.test_group_name, i), 'type': 'test'}
            response = self.do_post(self.base_groups_uri, data)
            self.assertEqual(response.status_code, 201)
            group_ids.append(response.data['id'])

        # create 5 users
        users = []
        for i in xrange(0, 5):
            data = {
                'email': 'test{}@example.com'.format(i),
                'username': 'test_user{}'.format(i),
                'password': 'test_pass',
                'first_name': 'John{}'.format(i),
                'last_name': 'Doe{}'.format(i)
            }
            response = self.do_post(self.base_users_uri, data)
            self.assertEqual(response.status_code, 201)
            users.append(response.data['id'])
            if i < 2:
                data = {'user_id': response.data['id']}
                response = self.do_post('{}{}/users'.format(self.base_groups_uri, group_ids[i]), data)
                self.assertEqual(response.status_code, 201)

        # enroll all users in course
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
        for user in users:
            data = {'user_id': user}
            response = self.do_post(test_uri, data)
            self.assertEqual(response.status_code, 201)

        # retrieve all users enrolled in the course and member of group 1
        response = self.do_get('{}?groups={}'.format(test_uri, group_ids[0]))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['enrollments']), 1)

        # retrieve all users enrolled in the course and member of group 1 and group 2
        response = self.do_get('{}?groups={},{}'.format(test_uri, group_ids[0], group_ids[1]))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['enrollments']), 2)

        # retrieve all users enrolled in the course and not member of group 1
        response = self.do_get('{}?exclude_groups={}'.format(test_uri, group_ids[0]))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['enrollments']), 4)

    def test_courses_users_detail_get(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
        test_user_uri = self.base_users_uri
        local_username = "some_test_user" + str(randint(11, 99))
        local_email = "test+notpending@tester.com"
        data = {
            'email': local_email,
            'username': local_username,
            'password': 'fooabr',
            'first_name': 'Joe',
            'last_name': 'Brown'
        }
        response = self.do_post(test_user_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        created_user_id = response.data['id']

        # Submit the query when unenrolled
        confirm_uri = '{}/{}'.format(test_uri, created_user_id)
        response = self.do_get(confirm_uri)
        self.assertEqual(response.status_code, 404)

        # now enroll this user in the course
        post_data = {}
        post_data['user_id'] = created_user_id
        response = self.do_post(test_uri, post_data)
        self.assertEqual(response.status_code, 201)
        confirm_uri = '{}/{}'.format(test_uri, created_user_id)
        response = self.do_get(confirm_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

    def test_courses_users_detail_get_invalid_course(self):
        test_uri = '{}/{}/users/{}'.format(self.base_courses_uri, self.test_bogus_course_id, self.users[0].id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
        self.assertGreater(len(response.data), 0)

    def test_courses_users_detail_get_invalid_user(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users/213432'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
        self.assertGreater(len(response.data), 0)

    def test_courses_users_detail_delete(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
        test_user_uri = self.base_users_uri
        local_username = "some_test_user" + str(randint(11, 99))
        local_email = "test+notpending@tester.com"
        data = {
            'email': local_email,
            'username': local_username,
            'password': 'fooabr',
            'first_name': 'Joe',
            'last_name': 'Brown'
        }
        response = self.do_post(test_user_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        created_user_id = response.data['id']

        # now enroll this user in the course
        post_data = {}
        post_data['user_id'] = created_user_id
        response = self.do_post(test_uri, post_data)
        self.assertEqual(response.status_code, 201)
        confirm_uri = '{}/{}'.format(test_uri, created_user_id)
        response = self.do_get(confirm_uri)
        self.assertEqual(response.status_code, 200)
        response = self.do_delete(confirm_uri)
        self.assertEqual(response.status_code, 204)

    def test_courses_users_detail_delete_invalid_course(self):
        test_uri = self.base_courses_uri + '/' + self.test_bogus_course_id + '/users/1'
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_users_detail_delete_invalid_user(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users/213432'
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_course_content_groups_list_post(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        data = {'name': 'Beta Group', 'type': 'project'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = '{}/{}/groups'.format(self.base_course_content_uri, unicode(self.course_project.scope_ids.usage_id))
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        confirm_uri = self.test_server_prefix + test_uri + '/' + str(group_id)
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['course_id'], str(self.test_course_id))
        self.assertEqual(response.data['content_id'], unicode(self.course_project.scope_ids.usage_id))
        self.assertEqual(response.data['group_id'], str(group_id))

    def test_course_content_groups_list_post_duplicate(self):
        data = {'name': 'Beta Group', 'type': 'project'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = '{}/{}/groups'.format(self.base_course_content_uri, unicode(self.course_project.scope_ids.usage_id))
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)

    def test_course_content_groups_list_post_invalid_course(self):
        data = {'name': 'Beta Group', 'type': 'project'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = '{}/{}/content/{}/groups'.format(
            self.base_courses_uri,
            self.test_bogus_course_id,
            unicode(self.course_project.scope_ids.usage_id)
        )
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_course_content_groups_list_post_invalid_content(self):
        data = {'name': 'Beta Group', 'type': 'project'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = '{}/{}/content/{}/groups'.format(
            self.base_courses_uri,
            self.test_course_id,
            self.test_bogus_content_id
        )
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_course_content_groups_list_post_invalid_group(self):
        test_uri = '{}/{}/content/{}/groups'.format(
            self.base_courses_uri,
            self.test_course_id,
            unicode(self.course_project.scope_ids.usage_id)
        )
        data = {'group_id': '12398721'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_course_content_groups_list_post_missing_group(self):
        test_uri = '{}/{}/content/{}/groups'.format(
            self.base_courses_uri,
            self.test_course_id,
            unicode(self.course_project.scope_ids.usage_id)
        )
        response = self.do_post(test_uri, {})
        self.assertEqual(response.status_code, 404)

    def test_course_content_groups_list_get(self):
        test_uri = '{}/{}/groups'.format(self.base_course_content_uri, unicode(self.course_project.scope_ids.usage_id))
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        alpha_group_id = response.data['id']
        data = {'group_id': alpha_group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)

        # Add a profile-less group to the system to offset the identifiers
        Group.objects.create(name='Offset Group')

        data = {'name': 'Beta Group', 'type': 'project'}
        response = self.do_post(self.base_groups_uri, data)

        data = {'name': 'Delta Group', 'type': 'project'}
        response = self.do_post(self.base_groups_uri, data)

        data = {'name': 'Gamma Group', 'type': 'project'}
        response = self.do_post(self.base_groups_uri, data)
        gamma_group_id = response.data['id']
        data = {'group_id': gamma_group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['group_id'], alpha_group_id)
        self.assertEqual(response.data[1]['group_id'], gamma_group_id)

        test_uri = test_uri + '?type=project'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_course_content_groups_list_get_invalid_course(self):
        test_uri = '{}/{}/content/{}/groups'.format(
            self.base_courses_uri,
            self.test_bogus_course_id,
            unicode(self.course_project.scope_ids.usage_id)
        )
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_content_groups_list_get_invalid_content(self):
        test_uri = '{}/{}/content/{}/groups'.format(
            self.base_courses_uri,
            self.test_course_id,
            self.test_bogus_content_id
        )
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_content_groups_list_get_filter_by_type(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        data = {'name': 'Beta Group', 'type': 'project'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        group_id = response.data['id']
        test_uri = '{}/{}/groups'.format(self.base_course_content_uri, unicode(self.course_project.scope_ids.usage_id))
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['group_id'], 2)

    def test_course_content_groups_detail_get(self):
        test_uri = '{}/{}/groups'.format(self.base_course_content_uri, unicode(self.course_project.scope_ids.usage_id))
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        data = {'name': 'Beta Group', 'type': 'project'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(response.data['uri'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['group_id'], str(group_id))

    def test_course_content_groups_detail_get_invalid_relationship(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = '{}/{}/groups/{}'.format(self.base_course_content_uri, unicode(self.course_project.scope_ids.usage_id), group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_content_groups_detail_get_invalid_course(self):
        test_uri = '{}/{}/content/{}/groups/123456'.format(
            self.base_courses_uri,
            self.test_bogus_course_id,
            unicode(self.course_project.scope_ids.usage_id)
        )
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_content_groups_detail_get_invalid_content(self):
        test_uri = '{}/{}/content/{}/groups/123456'.format(
            self.base_courses_uri,
            self.test_course_id,
            self.test_bogus_content_id
        )
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_content_groups_detail_get_invalid_group(self):
        test_uri = '{}/{}/content/{}/groups/123456'.format(
            self.base_courses_uri,
            self.test_course_id,
            unicode(self.course_project.scope_ids.usage_id)
        )
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_content_users_list_get(self):
        test_uri = '{}/{}/groups'.format(self.base_course_content_uri, unicode(self.course_project.scope_ids.usage_id))
        test_uri_users = '{}/{}/users'.format(self.base_course_content_uri, unicode(self.course_project.scope_ids.usage_id))
        test_course_users_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'

        # Create a group and add it to course module
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        group_id = response.data['id']
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        # Create another group and add it to course module
        data = {'name': 'Beta Group', 'type': 'project'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        another_group_id = response.data['id']
        data = {'group_id': another_group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        # create a 5 new users
        for i in xrange(1, 6):
            data = {
                'email': 'test{}@example.com'.format(i),
                'username': 'test_user{}'.format(i),
                'password': 'test_pass',
                'first_name': 'John{}'.format(i),
                'last_name': 'Doe{}'.format(i)
            }
            response = self.do_post(self.base_users_uri, data)
            self.assertEqual(response.status_code, 201)
            created_user_id = response.data['id']

            #add two users to Alpha Group and one to Beta Group and keep two without any group
            if i <= 3:
                add_to_group = group_id
                if i > 2:
                    add_to_group = another_group_id
                test_group_users_uri = '{}/{}/users'.format(self.base_groups_uri, add_to_group)

                data = {'user_id': created_user_id}
                response = self.do_post(test_group_users_uri, data)
                self.assertEqual(response.status_code, 201)
                #enroll one user in Alpha Group and one in Beta Group created user
                if i >= 2:
                    response = self.do_post(test_course_users_uri, data)
                    self.assertEqual(response.status_code, 201)
        response = self.do_get('{}?enrolled={}'.format(test_uri_users, 'True'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        response = self.do_get('{}?enrolled={}'.format(test_uri_users, 'False'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        #filter by group id
        response = self.do_get('{}?enrolled={}&group_id={}'.format(test_uri_users, 'true', group_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        response = self.do_get('{}?enrolled={}&group_id={}'.format(test_uri_users, 'false', group_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        #filter by group type
        response = self.do_get('{}?enrolled={}&type={}'.format(test_uri_users, 'true', 'project'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_course_content_users_list_get_invalid_course_and_content(self):
        invalid_course_uri = '{}/{}/content/{}/users'.format(self.base_courses_uri, self.test_bogus_course_id, unicode(self.course_project.scope_ids.usage_id))
        response = self.do_get(invalid_course_uri)
        self.assertEqual(response.status_code, 404)

        invalid_content_uri = '{}/{}/content/{}/users'.format(self.base_courses_uri, self.test_course_id, self.test_bogus_content_id)
        response = self.do_get(invalid_content_uri)
        self.assertEqual(response.status_code, 404)

    def test_coursemodulecompletions_post(self):

        data = {
            'email': 'test@example.com',
            'username': 'test_user',
            'password': 'test_pass',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        response = self.do_post(self.base_users_uri, data)
        self.assertEqual(response.status_code, 201)
        created_user_id = response.data['id']
        completions_uri = '{}/{}/completions/'.format(self.base_courses_uri, unicode(self.course.id))
        stage = 'First'
        completions_data = {'content_id': unicode(self.course_content.scope_ids.usage_id), 'user_id': created_user_id, 'stage': stage}
        response = self.do_post(completions_uri, completions_data)
        self.assertEqual(response.status_code, 201)
        coursemodulecomp_id = response.data['id']
        self.assertGreater(coursemodulecomp_id, 0)
        self.assertEqual(response.data['user_id'], created_user_id)
        self.assertEqual(response.data['course_id'], unicode(self.course.id))
        self.assertEqual(response.data['content_id'], unicode(self.course_content.scope_ids.usage_id))
        self.assertEqual(response.data['stage'], stage)
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

        # test to create course completion with same attributes
        response = self.do_post(completions_uri, completions_data)
        self.assertEqual(response.status_code, 409)

        # test to create course completion with empty user_id
        completions_data['user_id'] = None
        response = self.do_post(completions_uri, completions_data)
        self.assertEqual(response.status_code, 400)

        # test to create course completion with empty content_id
        completions_data['content_id'] = None
        response = self.do_post(completions_uri, completions_data)
        self.assertEqual(response.status_code, 400)

        # test to create course completion with invalid content_id
        completions_data['content_id'] = self.test_bogus_content_id
        response = self.do_post(completions_uri, completions_data)
        self.assertEqual(response.status_code, 400)

    def test_course_module_completions_post_invalid_course(self):
        completions_uri = '{}/{}/completions/'.format(self.base_courses_uri, self.test_bogus_course_id)
        completions_data = {'content_id': unicode(self.course_content.scope_ids.usage_id), 'user_id': self.users[0].id}
        response = self.do_post(completions_uri, completions_data)
        self.assertEqual(response.status_code, 404)

    def test_course_module_completions_post_invalid_content(self):
        completions_uri = '{}/{}/completions/'.format(self.base_courses_uri, self.test_course_id)
        completions_data = {'content_id': self.test_bogus_content_id, 'user_id': self.users[0].id}
        response = self.do_post(completions_uri, completions_data)
        self.assertEqual(response.status_code, 400)

    def test_coursemodulecompletions_filters(self):
        completion_uri = '{}/{}/completions/'.format(self.base_courses_uri, unicode(self.course.id))
        for i in xrange(1, 3):
            data = {
                'email': 'test{}@example.com'.format(i),
                'username': 'test_user{}'.format(i),
                'password': 'test_pass',
                'first_name': 'John{}'.format(i),
                'last_name': 'Doe{}'.format(i)
            }
            response = self.do_post(self.base_users_uri, data)
            self.assertEqual(response.status_code, 201)
            created_user_id = response.data['id']

        for i in xrange(1, 26):
            local_content_name = 'Video_Sequence{}'.format(i)
            local_content = ItemFactory.create(
                category="videosequence",
                parent_location=self.chapter.location,
                data=self.test_data,
                display_name=local_content_name
            )
            content_id = unicode(local_content.scope_ids.usage_id)
            if i < 25:
                content_id = unicode(self.course_content.scope_ids.usage_id) + str(i)
                stage = None
            else:
                content_id = unicode(self.course_content.scope_ids.usage_id)
                stage = 'Last'
            completions_data = {'content_id': content_id, 'user_id': created_user_id, 'stage': stage}
            response = self.do_post(completion_uri, completions_data)
            self.assertEqual(response.status_code, 201)

        #filter course module completion by user
        user_filter_uri = '{}?user_id={}&page_size=10&page=3'.format(completion_uri, created_user_id)
        response = self.do_get(user_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['num_pages'], 3)

        #filter course module completion by multiple user ids
        user_filter_uri = '{}?user_id={}'.format(completion_uri, str(created_user_id) + ',3,4')
        response = self.do_get(user_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['results']), 20)
        self.assertEqual(response.data['num_pages'], 2)

        #filter course module completion by user who has not completed any course module
        user_filter_uri = '{}?user_id={}'.format(completion_uri, 1)
        response = self.do_get(user_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        #filter course module completion by course_id
        course_filter_uri = '{}?course_id={}&page_size=10'.format(completion_uri, unicode(self.course.id))
        response = self.do_get(course_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['results']), 10)

        #filter course module completion by content_id
        content_id = {'content_id': '{}1'.format(unicode(self.course_content.scope_ids.usage_id))}
        content_filter_uri = '{}?{}'.format(completion_uri, urlencode(content_id))
        response = self.do_get(content_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

        #filter course module completion by invalid content_id
        content_id = {'content_id': '{}1'.format(self.test_bogus_content_id)}
        content_filter_uri = '{}?{}'.format(completion_uri, urlencode(content_id))
        response = self.do_get(content_filter_uri)
        self.assertEqual(response.status_code, 404)

        #filter course module completion by stage
        content_filter_uri = '{}?stage={}'.format(completion_uri, 'Last')
        response = self.do_get(content_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

    def test_coursemodulecompletions_get_invalid_course(self):
        completion_uri = '{}/{}/completions/'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_get(completion_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_metrics_social_get(self):
        test_uri = '{}/{}/metrics/social/'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data.keys()), 2)
        users = response.data['users']
        self.assertTrue(users.get('1'))
        self.assertTrue(users.get('2'))

        # make the first user an observer to asset that its content is being filtered out from
        # the aggregates
        allow_access(self.course, self.users[0], 'observer')

        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data.keys()), 1)
        users = response.data['users']
        self.assertFalse(users.get('1'))
        self.assertTrue(users.get('2'))

    def test_courses_metrics_grades_leaders_list_get(self):
        # make the last user an observer to asset that its content is being filtered out from
        # the aggregates
        expected_course_average = 0.398
        allow_access(self.course, self.users[USER_COUNT-1], 'observer')

        item = ItemFactory.create(
            parent_location=self.chapter.location,
            category='mentoring',
            data=StringResponseXMLFactory().build_xml(answer='foo'),
            display_name=u"test problem same points",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Midterm Exam"}
        )

        points_scored = 2.25
        points_possible = 4
        user = self.users[USER_COUNT - 3]
        module = self.get_module_for_user(user, self.course, item)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
        module.system.publish(module, 'grade', grade_dict)

        points_scored = 2.25
        points_possible = 4
        user = self.users[USER_COUNT - 2]
        module = self.get_module_for_user(user, self.course, item)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
        module.system.publish(module, 'grade', grade_dict)

        test_uri = '{}/{}/metrics/grades/leaders/'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['leaders']), 3)
        self.assertEqual(response.data['leaders'][0]['username'], 'testuser4')
        self.assertEqual(response.data['course_avg'], expected_course_average)

        count_filter_test_uri = '{}?count=4'.format(test_uri)
        response = self.do_get(count_filter_test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['leaders']), 4)

        # Filter by user_id, include a user with the exact same score
        user200 = UserFactory.create(username="testuser200", profile='test')
        CourseEnrollmentFactory.create(user=user200, course_id=self.course.id)

        self.midterm = ItemFactory.create(
            parent_location=self.chapter.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name='Problem 200',
            metadata={'rerandomize': 'always', 'graded': True, 'format': 'Midterm Exam'}
        )
        points_scored = 100
        points_possible = 100
        module = self.get_module_for_user(user200, self.course, self.midterm)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user200.id}
        module.system.publish(module, 'grade', grade_dict)
        StudentModuleFactory.create(
            course_id=self.course.id,
            module_type='sequential',
            module_state_key=self.midterm.location,
        )
        self.final = ItemFactory.create(
            parent_location=self.chapter.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name='Problem 201',
            metadata={'rerandomize': 'always', 'graded': True, 'format': 'Final Exam'}
        )
        points_scored = 100
        points_possible = 100
        module = self.get_module_for_user(user200, self.course, self.final)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user200.id}
        module.system.publish(module, 'grade', grade_dict)
        StudentModuleFactory.create(
            course_id=self.course.id,
            module_type='sequential',
            module_state_key=self.final.location,
        )
        points_scored = 50
        points_possible = 100
        module = self.get_module_for_user(user200, self.course, item)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user200.id}
        module.system.publish(module, 'grade', grade_dict)

        user_filter_uri = '{}?user_id={}&count=10'.format(test_uri, self.users[1].id)
        response = self.do_get(user_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['leaders']), 6)
        self.assertEqual(response.data['course_avg'], 0.378)
        self.assertEqual(response.data['user_position'], 4)
        self.assertEqual(response.data['user_grade'], 0.28)

        # Filter by user who has never accessed a course module
        test_user = UserFactory.create(username="testusernocoursemod")
        CourseEnrollmentFactory.create(user=test_user, course_id=self.course.id)
        user_filter_uri = '{}?user_id={}'.format(test_uri, test_user.id)
        response = self.do_get(user_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user_grade'], 0)
        self.assertEqual(response.data['user_position'], 7)
        # Also, with this new user now added the course average should be different
        self.assertNotEqual(response.data['course_avg'], expected_course_average)
        rounded_avg = float("{0:.2f}".format(response.data['course_avg']))
        self.assertEqual(rounded_avg, 0.32)

        # test with bogus course
        bogus_test_uri = '{}/{}/metrics/grades/leaders/'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_get(bogus_test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_metrics_grades_leaders_list_get_empty_course(self):
        test_uri = '{}/{}/metrics/grades/leaders/'.format(self.base_courses_uri, unicode(self.empty_course.id))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['course_avg'], 0)
        self.assertEqual(len(response.data['leaders']), 0)

    def test_courses_completions_leaders_list_get(self):
        course = CourseFactory.create(
            number='4033',
            name='leaders_by_completions',
            start=datetime(2014, 9, 16, 14, 30),
            end=datetime(2015, 1, 16)
        )

        chapter = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=self.test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )

        sub_section = ItemFactory.create(
            parent_location=chapter.location,
            category="sequential",
            display_name=u"test subsection",
        )
        unit = ItemFactory.create(
            parent_location=sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test unit",
        )

        # create 5 users
        USER_COUNT = 5
        users = [UserFactory.create(username="testuser_cctest" + str(__), profile='test') for __ in xrange(USER_COUNT)]

        for user in users:
            CourseEnrollmentFactory.create(user=user, course_id=course.id)
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        test_course_id = unicode(course.id)
        completion_uri = '{}/{}/completions/'.format(self.base_courses_uri, test_course_id)
        leaders_uri = '{}/{}/metrics/completions/leaders/'.format(self.base_courses_uri, test_course_id)
        # Make last user as observer to make sure that data is being filtered out
        allow_access(course, users[USER_COUNT-1], 'observer')

        contents = []
        for i in xrange(1, 26):
            local_content_name = 'Video_Sequence{}'.format(i)
            local_content = ItemFactory.create(
                category="videosequence",
                parent_location=unit.location,
                data=self.test_data,
                display_name=local_content_name
            )
            contents.append(local_content)
            if i < 3:
                user_id = users[0].id
            elif i < 10:
                user_id = users[1].id
            elif i < 17:
                user_id = users[2].id
            else:
                user_id = users[3].id

            content_id = unicode(local_content.scope_ids.usage_id)
            completions_data = {'content_id': content_id, 'user_id': user_id}
            response = self.do_post(completion_uri, completions_data)
            self.assertEqual(response.status_code, 201)

            # observer should complete everything, so we can assert that it is filtered out
            response = self.do_post(completion_uri, {
                'content_id': content_id, 'user_id': users[USER_COUNT-1].id
            })
            self.assertEqual(response.status_code, 201)

        expected_course_avg = '25.000'
        test_uri = '{}?count=6'.format(leaders_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['leaders']), 4)
        self.assertEqual('{0:.3f}'.format(response.data['course_avg']), expected_course_avg)

        # without count filter and user_id
        test_uri = '{}?user_id={}'.format(leaders_uri, users[1].id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['leaders']), 4)
        self.assertEqual(response.data['position'], 2)
        self.assertEqual('{0:.3f}'.format(response.data['completions']), '28.000')

        # with skipleaders filter
        test_uri = '{}?user_id={}&skipleaders=true'.format(leaders_uri, users[1].id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data.get('leaders', None))
        self.assertEqual('{0:.3f}'.format(response.data['course_avg']), expected_course_avg)
        self.assertEqual('{0:.3f}'.format(response.data['completions']), '28.000')

        # test with bogus course
        test_uri = '{}/{}/metrics/completions/leaders/'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

        #filter course module completion by organization
        data = {
            'name': 'Test Organization',
            'display_name': 'Test Org Display Name',
            'users': [users[1].id]
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}?organizations={}'.format(leaders_uri, response.data['id'])
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['leaders']), 1)
        self.assertEqual(response.data['leaders'][0]['id'], users[1].id)
        self.assertEqual('{0:.3f}'.format(response.data['leaders'][0]['completions']), '28.000')
        self.assertEqual('{0:.3f}'.format(response.data['course_avg']), '28.000')

        # test with unknown user
        test_uri = '{}?user_id={}&skipleaders=true'.format(leaders_uri, '909999')
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data.get('leaders', None))
        self.assertEqual(response.data['position'], 0)
        self.assertEqual(response.data['completions'], 0)

        # test a case where completions are greater than total course modules. it should not be more than 100
        contents.append(self.course_content)
        for content in contents[2:]:
            user_id = users[0].id
            content_id = unicode(content.scope_ids.usage_id)
            completions_data = {'content_id': content_id, 'user_id': user_id}
            response = self.do_post(completion_uri, completions_data)
            self.assertEqual(response.status_code, 201)

        test_uri = '{}?user_id={}'.format(leaders_uri, users[0].id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('{0:.3f}'.format(response.data['completions']), '100.000')


    def test_courses_metrics_grades_list_get(self):
        # Retrieve the list of grades for this course
        # All the course/item/user scaffolding was handled in Setup
        test_uri = '{}/{}/metrics/grades'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data['grade_average'], 0)
        self.assertGreater(response.data['grade_maximum'], 0)
        self.assertGreater(response.data['grade_minimum'], 0)
        self.assertEqual(response.data['grade_count'], USER_COUNT)
        self.assertGreater(response.data['course_grade_average'], 0)
        self.assertGreater(response.data['course_grade_maximum'], 0)
        self.assertGreater(response.data['course_grade_minimum'], 0)
        self.assertEqual(response.data['course_grade_count'], USER_COUNT)
        self.assertEqual(len(response.data['grades']), USER_COUNT)

        # Filter by user_id
        user_filter_uri = '{}?user_id=1,3'.format(test_uri)
        response = self.do_get(user_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data['grade_average'], 0)
        self.assertGreater(response.data['grade_maximum'], 0)
        self.assertGreater(response.data['grade_minimum'], 0)
        self.assertEqual(response.data['grade_count'], 2)
        self.assertGreater(response.data['course_grade_average'], 0)
        self.assertGreater(response.data['course_grade_maximum'], 0)
        self.assertGreater(response.data['course_grade_minimum'], 0)
        self.assertEqual(response.data['course_grade_count'], USER_COUNT)
        self.assertEqual(len(response.data['grades']), 2)

        # make the last user an observer to asset that its content is being filtered out from
        # the aggregates
        user_index = USER_COUNT - 1
        allow_access(self.course, self.users[user_index], 'observer')
        test_uri = '{}/{}/metrics/grades'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['grades']), user_index)

    def test_courses_metrics_grades_list_get_empty_course(self):
        # Retrieve the list of grades for this course
        # All the course/item/user scaffolding was handled in Setup
        test_uri = '{}/{}/metrics/grades'.format(self.base_courses_uri, unicode(self.empty_course.id))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['grade_count'], 0)
        self.assertEqual(response.data['course_grade_maximum'], 0)

    def test_courses_grades_list_get_invalid_course(self):
        # Retrieve the list of grades for this course
        # All the course/item/user scaffolding was handled in Setup
        test_uri = '{}/{}/grades'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_project_list(self):
        projects_uri = self.base_projects_uri

        for i in xrange(0, 25):
            local_content_name = 'Video_Sequence{}'.format(i)
            local_content = ItemFactory.create(
                category="videosequence",
                parent_location=self.chapter.location,
                data=self.test_data,
                display_name=local_content_name
            )
            # location:MITx+999+Robot_Super_Course+videosequence+Video_Sequence0
            data = {
                'content_id': unicode(local_content.scope_ids.usage_id),
                'course_id': self.test_course_id
            }
            response = self.do_post(projects_uri, data)
            self.assertEqual(response.status_code, 201)

        response = self.do_get('{}/{}/projects/?page_size=10'.format(self.base_courses_uri, self.test_course_id))
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['num_pages'], 3)

    def test_courses_data_metrics(self):
        test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
        completion_uri = '{}/{}/completions/'.format(self.base_courses_uri, unicode(self.course.id))
        test_user_uri = self.base_users_uri
        users_to_add = 5
        for i in xrange(0, users_to_add):
            data = {
                'email': 'test{}@example.com'.format(i), 'username': 'test_user{}'.format(i),
                'password': 'test_password'
            }
            # create a new user
            response = self.do_post(test_user_uri, data)
            self.assertEqual(response.status_code, 201)
            created_user_id = response.data['id']

            # now enroll this user in the course
            post_data = {'user_id': created_user_id}
            response = self.do_post(test_uri, post_data)
            self.assertEqual(response.status_code, 201)

        #create an organization
        data = {
            'name': 'Test Organization',
            'display_name': 'Test Org Display Name',
            'users': [created_user_id]
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        org_id = response.data['id']

        for i in xrange(1, 5):
            local_content_name = 'Video_Sequence{}'.format(i)
            local_content = ItemFactory.create(
                category="videosequence",
                parent_location=self.chapter.location,
                data=self.test_data,
                display_name=local_content_name
            )
            content_id = unicode(local_content.scope_ids.usage_id)
            completions_data = {'content_id': content_id, 'user_id': created_user_id, 'stage': None}
            response = self.do_post(completion_uri, completions_data)
            self.assertEqual(response.status_code, 201)

        # get course metrics
        course_metrics_uri = '{}/{}/metrics/'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_get(course_metrics_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['users_enrolled'], users_to_add + USER_COUNT)
        self.assertEqual(response.data['users_started'], 1)
        self.assertIsNotNone(response.data['grade_cutoffs'])
        # TODO: (mattdrayer) Uncomment after comment service has been updated
        # self.assertEqual(response.data['num_threads'], 5)
        # self.assertEqual(response.data['num_active_threads'], 3)

        # get course metrics by organization
        course_metrics_uri = '{}/{}/metrics/?organization={}'.format(self.base_courses_uri, self.test_course_id, org_id)
        response = self.do_get(course_metrics_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['users_enrolled'], 1)
        self.assertEqual(response.data['users_started'], 1)

        # test with bogus course
        course_metrics_uri = '{}/{}/metrics/'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_get(course_metrics_uri)
        self.assertEqual(response.status_code, 404)

    @mock.patch.dict("django.conf.settings.FEATURES", {'MARK_PROGRESS_ON_GRADING_EVENT': True,
                                                       'SIGNAL_ON_SCORE_CHANGED': True,
                                                       'STUDENT_GRADEBOOK': True,
                                                       'STUDENT_PROGRESS': True})
    def test_courses_data_time_series_metrics(self):
        course = CourseFactory.create(
            number='3033',
            name='metrics_in_timeseries',
            start=datetime(2014, 9, 16, 14, 30),
            end=datetime(2015, 1, 16)
        )

        chapter = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=self.test_data,
            due=datetime(2015, 5, 16, 14, 30),
            display_name="Overview"
        )

        sub_section = ItemFactory.create(
            parent_location=chapter.location,
            category="sequential",
            display_name=u"test subsection",
        )
        unit = ItemFactory.create(
            parent_location=sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test unit",
        )

        item = ItemFactory.create(
            parent_location=unit.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name='Problem to test timeseries',
            metadata={'rerandomize': 'always', 'graded': True, 'format': 'Midterm Exam'}
        )

        item2 = ItemFactory.create(
            parent_location=unit.location,
            category='problem 2',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name='Problem 2 for test timeseries',
            metadata={'rerandomize': 'always', 'graded': True, 'format': 'Final Exam'}
        )

        # create 10 users
        USER_COUNT = 25
        users = [UserFactory.create(username="testuser_tstest" + str(__), profile='test') for __ in xrange(USER_COUNT)]
        user_ids = [user.id for user in users]

        #create an organization
        data = {
            'name': 'Test Organization',
            'display_name': 'Test Org Display Name',
            'users': user_ids
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        org_id = response.data['id']

        # enroll users with time set to 28 days ago
        enrolled_time = timezone.now() + relativedelta(days=-28)
        with freeze_time(enrolled_time):
            for user in users:
                CourseEnrollmentFactory.create(user=user, course_id=course.id)

        points_scored = .25
        points_possible = 1
        grade_dict = {'value': points_scored, 'max_value': points_possible}

        # Mark users as those who have started course
        for j, user in enumerate(users):
            complete_time = timezone.now() + relativedelta(days=-(USER_COUNT - j))
            with freeze_time(complete_time):
                module = self.get_module_for_user(user, course, item)
                grade_dict['user_id'] = user.id
                module.system.publish(module, 'grade', grade_dict)

                # Last 2 users as those who have completed
                if j >= USER_COUNT - 2:
                    try:
                        sg_entry = StudentGradebook.objects.get(user=user, course_id=course.id)
                        sg_entry.grade = 0.9
                        sg_entry.proforma_grade = 0.91
                        sg_entry.save()
                    except StudentGradebook.DoesNotExist:
                        StudentGradebook.objects.create(user=user, course_id=course.id, grade=0.9,
                                                        proforma_grade=0.91)

        # make more completions
        for j, user in enumerate(users[:5]):
            complete_time = timezone.now() + relativedelta(days=-(USER_COUNT - j))
            with freeze_time(complete_time):
                module = self.get_module_for_user(user, course, item2)
                grade_dict['user_id'] = user.id
                module.system.publish(module, 'grade', grade_dict)

        test_course_id = unicode(course.id)
        # get course metrics in time series format
        end_date = datetime.now().date()
        start_date = end_date + relativedelta(days=-4)
        course_metrics_uri = '{}/{}/time-series-metrics/?start_date={}&end_date={}&organization={}'\
            .format(self.base_courses_uri,
                    test_course_id,
                    start_date,
                    end_date,
                    org_id)

        response = self.do_get(course_metrics_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['users_not_started']), 5)
        total_not_started = sum([not_started[1] for not_started in response.data['users_not_started']])
        self.assertEqual(total_not_started, 6)
        self.assertEqual(len(response.data['users_started']), 5)
        total_started = sum([started[1] for started in response.data['users_started']])
        self.assertEqual(total_started, 4)
        self.assertEqual(len(response.data['users_completed']), 5)
        total_completed = sum([completed[1] for completed in response.data['users_completed']])
        self.assertEqual(total_completed, 2)
        self.assertEqual(len(response.data['modules_completed']), 5)
        total_modules_completed = sum([completed[1] for completed in response.data['modules_completed']])
        self.assertEqual(total_modules_completed, 4)
        self.assertEqual(len(response.data['active_users']), 5)
        total_active = sum([active[1] for active in response.data['active_users']])
        self.assertEqual(total_active, 5)
        self.assertEqual(response.data['users_enrolled'][0][1], 25)

        # get modules completed for first 5 days
        start_date = datetime.now().date() + relativedelta(days=-USER_COUNT)
        end_date = datetime.now().date() + relativedelta(days=-(USER_COUNT - 4))
        course_metrics_uri = '{}/{}/time-series-metrics/?start_date={}&end_date={}'.format(self.base_courses_uri,
                                                                                           test_course_id,
                                                                                           start_date,
                                                                                           end_date)

        response = self.do_get(course_metrics_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['modules_completed']), 5)
        total_modules_completed = sum([completed[1] for completed in response.data['modules_completed']])
        self.assertEqual(total_modules_completed, 10)

        # metrics with weeks as interval
        end_date = datetime.now().date()
        start_date = end_date + relativedelta(weeks=-2)
        course_metrics_uri = '{}/{}/time-series-metrics/?start_date={}&end_date={}&' \
                             'interval=weeks'.format(self.base_courses_uri,
                                                     test_course_id,
                                                     start_date,
                                                     end_date)

        response = self.do_get(course_metrics_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['users_not_started']), 2)
        self.assertGreaterEqual(len(response.data['users_started']), 2)
        self.assertGreaterEqual(len(response.data['users_completed']), 2)

        # metrics with months as interval
        start_date = end_date + relativedelta(months=-3)
        end_date = datetime.now().date() + relativedelta(months=1)
        course_metrics_uri = '{}/{}/time-series-metrics/?start_date={}&end_date={}&' \
                             'interval=months'.format(self.base_courses_uri,
                                                      test_course_id,
                                                      start_date,
                                                      end_date)

        response = self.do_get(course_metrics_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['users_not_started']), 5)
        self.assertEqual(len(response.data['users_started']), 5)
        self.assertEqual(len(response.data['users_completed']), 5)

        # test without end_date
        course_metrics_uri = '{}/{}/time-series-metrics/?start_date={}'.format(self.base_courses_uri,
                                                                                           test_course_id,
                                                                                           start_date)
        response = self.do_get(course_metrics_uri)
        self.assertEqual(response.status_code, 400)

        # test with unsupported interval
        course_metrics_uri = '{}/{}/time-series-metrics/?start_date={}&end_date={}&interval=hours'\
            .format(self.base_courses_uri,
                    test_course_id,
                    start_date,
                    end_date)

        response = self.do_get(course_metrics_uri)
        self.assertEqual(response.status_code, 400)

        # Test after un-enrolling some users
        test_uri = self.base_courses_uri + '/' + test_course_id + '/users'
        for j, user in enumerate(users[-5:]):
            response = self.do_delete('{}/{}'.format(test_uri, user.id))
            self.assertEqual(response.status_code, 204)
        end_date = datetime.now().date()
        start_date = end_date + relativedelta(days=-4)
        course_metrics_uri = '{}/{}/time-series-metrics/?start_date={}&end_date={}'\
            .format(self.base_courses_uri,
                    test_course_id,
                    start_date,
                    end_date)

        response = self.do_get(course_metrics_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['users_not_started']), 5)
        total_not_started = sum([not_started[1] for not_started in response.data['users_not_started']])
        self.assertEqual(total_not_started, 0)
        self.assertEqual(len(response.data['users_started']), 5)
        total_started = sum([started[1] for started in response.data['users_started']])
        self.assertEqual(total_started, 0)
        self.assertEqual(len(response.data['users_completed']), 5)
        total_completed = sum([completed[1] for completed in response.data['users_completed']])
        self.assertEqual(total_completed, 0)
        self.assertEqual(len(response.data['modules_completed']), 5)
        total_modules_completed = sum([completed[1] for completed in response.data['modules_completed']])
        self.assertEqual(total_modules_completed, 0)
        self.assertEqual(len(response.data['active_users']), 5)
        total_active = sum([active[1] for active in response.data['active_users']])
        self.assertEqual(total_active, 0)
        self.assertEqual(response.data['users_enrolled'][0][1], 20)

    def test_course_workgroups_list(self):
        projects_uri = self.base_projects_uri
        data = {
            'course_id': self.test_course_id,
            'content_id': 'self.test_course_content_id'
        }
        response = self.do_post(projects_uri, data)
        self.assertEqual(response.status_code, 201)
        project_id = response.data['id']

        test_workgroups_uri = self.base_workgroups_uri
        for i in xrange(1, 12):
            data = {
                'name': '{} {}'.format('Workgroup', i),
                'project': project_id
            }
            response = self.do_post(test_workgroups_uri, data)
            self.assertEqual(response.status_code, 201)

        # get workgroups associated to course
        test_uri = '{}/{}/workgroups/?page_size=10'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.data['count'], 11)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['num_pages'], 2)

        # test with bogus course
        test_uri = '{}/{}/workgroups/'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_course_users_count_by_city(self):
        test_uri = self.base_users_uri

        # create a 25 new users
        for i in xrange(1, 26):
            if i < 10:
                city = 'San Francisco'
            elif i < 15:
                city = 'Denver'
            elif i < 20:
                city = 'Dallas'
            else:
                city = 'New York City'
            data = {
                'email': 'test{}@example.com'.format(i), 'username': 'test_user{}'.format(i),
                'password': 'test.me!',
                'first_name': '{} {}'.format('John', i), 'last_name': '{} {}'.format('Doe', i), 'city': city,
                'country': 'PK', 'level_of_education': 'b', 'year_of_birth': '2000', 'gender': 'male',
                'title': 'Software Engineer', 'avatar_url': 'http://example.com/avatar.png'
            }

            response = self.do_post(test_uri, data)
            self.assertEqual(response.status_code, 201)
            created_user_id = response.data['id']
            user_uri = response.data['uri']
            # now enroll this user in the course
            post_data = {'user_id': created_user_id}
            courses_test_uri = self.base_courses_uri + '/' + self.test_course_id + '/users'
            response = self.do_post(courses_test_uri, post_data)
            self.assertEqual(response.status_code, 201)

            response = self.do_get(user_uri)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['city'], city)

        # make all the classwide users an observer to assert that its content is being filtered out from
        # the aggregates
        for user in self.users:
            allow_access(self.course, user, 'observer')

        response = self.do_get('{}/{}/metrics/cities/'.format(self.base_courses_uri, self.test_course_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 4)
        self.assertEqual(response.data['results'][0]['city'], 'San Francisco')
        self.assertEqual(response.data['results'][0]['count'], 9)

        # filter counts by city
        sf_uri = '{}/{}/metrics/cities/?city=new york city, San Francisco'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_get(sf_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['city'], 'San Francisco')
        self.assertEqual(response.data['results'][0]['count'], 9)
        self.assertEqual(response.data['results'][1]['city'], 'New York City')
        self.assertEqual(response.data['results'][1]['count'], 6)

        # filter counts by city
        dnv_uri = '{}/{}/metrics/cities/?city=Denver'.format(self.base_courses_uri, self.test_course_id)
        response = self.do_get(dnv_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['city'], 'Denver')
        self.assertEqual(response.data['results'][0]['count'], 5)

        # Do a get with a bogus course to hit the 404 case
        response = self.do_get('{}/{}/metrics/cities/'.format(self.base_courses_uri, self.test_bogus_course_id))
        self.assertEqual(response.status_code, 404)

    def test_courses_roles_list_get(self):
        allow_access(self.course, self.users[0], 'staff')
        allow_access(self.course, self.users[1], 'instructor')
        allow_access(self.course, self.users[2], 'observer')
        test_uri = '{}/{}/roles/'.format(self.base_courses_uri, unicode(self.course.id))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

        # filter roleset by user
        user_id = {'user_id': '{}'.format(self.users[0].id)}
        user_filter_uri = '{}?{}'.format(test_uri, urlencode(user_id))
        response = self.do_get(user_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        # filter roleset by role
        role = {'role': 'instructor'}
        role_filter_uri = '{}?{}'.format(test_uri, urlencode(role))
        response = self.do_get(role_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        role = {'role': 'invalid_role'}
        role_filter_uri = '{}?{}'.format(test_uri, urlencode(role))
        response = self.do_get(role_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_courses_roles_list_get_invalid_course(self):
        test_uri = '{}/{}/roles/'.format(self.base_courses_uri, self.test_bogus_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_roles_list_post(self):
        test_uri = '{}/{}/roles/'.format(self.base_courses_uri, unicode(self.course.id))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        data = {'user_id': self.users[0].id, 'role': 'instructor'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        # Confirm this user also has forum moderation permissions
        role = Role.objects.get(course_id=self.course.id, name=FORUM_ROLE_MODERATOR)
        has_role = role.users.get(id=self.users[0].id)
        self.assertTrue(has_role)

    def test_courses_roles_list_post_invalid_course(self):
        test_uri = '{}/{}/roles/'.format(self.base_courses_uri, self.test_bogus_course_id)
        data = {'user_id': self.users[0].id, 'role': 'instructor'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_courses_roles_list_post_invalid_user(self):
        test_uri = '{}/{}/roles/'.format(self.base_courses_uri, unicode(self.course.id))
        data = {'user_id': 23423, 'role': 'instructor'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_courses_roles_list_post_invalid_role(self):
        test_uri = '{}/{}/roles/'.format(self.base_courses_uri, unicode(self.course.id))
        data = {'user_id': self.users[0].id, 'role': 'invalid_role'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_courses_roles_users_detail_delete(self):
        test_uri = '{}/{}/roles/'.format(self.base_courses_uri, unicode(self.course.id))
        data = {'user_id': self.users[0].id, 'role': 'instructor'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(test_uri)
        self.assertEqual(len(response.data), 1)

        delete_uri = '{}instructor/users/{}'.format(test_uri, self.users[0].id)
        response = self.do_delete(delete_uri)
        self.assertEqual(response.status_code, 204)

        response = self.do_get(test_uri)
        self.assertEqual(len(response.data), 0)

        # Confirm this user no longer has forum moderation permissions
        role = Role.objects.get(course_id=self.course.id, name=FORUM_ROLE_MODERATOR)
        try:
            has_role = role.users.get(id=self.users[0].id)
            self.assertTrue(False)
        except ObjectDoesNotExist:
            pass

    def test_courses_roles_users_detail_delete_invalid_course(self):
        test_uri = '{}/{}/roles/'.format(self.base_courses_uri, self.test_bogus_course_id)
        delete_uri = '{}instructor/users/{}'.format(test_uri, self.users[0].id)
        response = self.do_delete(delete_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_roles_users_detail_delete_invalid_user(self):
        test_uri = '{}/{}/roles/'.format(self.base_courses_uri, unicode(self.course.id))
        delete_uri = '{}instructor/users/291231'.format(test_uri)
        response = self.do_delete(delete_uri)
        self.assertEqual(response.status_code, 404)

    def test_courses_roles_users_detail_delete_invalid_role(self):
        test_uri = '{}/{}/roles/'.format(self.base_courses_uri, unicode(self.course.id))
        delete_uri = '{}invalid_role/users/{}'.format(test_uri, self.users[0].id)
        response = self.do_delete(delete_uri)
        self.assertEqual(response.status_code, 404)
