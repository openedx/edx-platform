# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/projects/tests/test_workgroups.py]
"""
from datetime import datetime
import json
import uuid
from urllib import urlencode

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import Client
from django.test.utils import override_settings

from api_manager.models import GroupProfile
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from projects.models import Project, Workgroup
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from openedx.core.djangoapps.course_groups.cohorts import (get_cohort_by_name, remove_user_from_cohort,
                                   delete_empty_cohort, is_user_in_cohort, get_course_cohort_names)
from openedx.core.djangoapps.course_groups.models import CourseUserGroup

TEST_API_KEY = str(uuid.uuid4())


class SecureClient(Client):

    """ Django test client using a "secure" connection. """

    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update({'SERVER_PORT': 443, 'wsgi.url_scheme': 'https'})
        super(SecureClient, self).__init__(*args, **kwargs)

    def delete_with_data(self, *args, **kwargs):
        """ Construct a DELETE request that includes data."""
        kwargs.update({'REQUEST_METHOD': 'DELETE'})
        return super(SecureClient, self).put(*args, **kwargs)


@override_settings(EDX_API_KEY=TEST_API_KEY)
class WorkgroupsApiTests(ModuleStoreTestCase):

    """ Test suite for Users API views """

    def setUp(self):
        super(WorkgroupsApiTests, self).setUp()
        self.test_server_prefix = 'https://testserver'
        self.test_workgroups_uri = '/api/server/workgroups/'
        self.test_submissions_uri = '/api/server/submissions/'
        self.test_peer_reviews_uri = '/api/server/peer_reviews/'
        self.test_workgroup_reviews_uri = '/api/server/workgroup_reviews/'
        self.test_courses_uri = '/api/server/courses'
        self.test_bogus_course_id = 'foo/bar/baz'
        self.test_bogus_course_content_id = "i4x://foo/bar/baz"
        self.test_group_id = '1'
        self.test_bogus_group_id = "2131241123"
        self.test_workgroup_name = str(uuid.uuid4())

        self.test_course = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16, 14, 30)
        )
        self.test_data = '<html>{}</html>'.format(str(uuid.uuid4()))

        self.test_group_project = ItemFactory.create(
            category="group_project",
            parent_location=self.test_course.location,
            data=self.test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Group Project"
        )

        self.test_course_id = unicode(self.test_course.id)
        self.test_course_content_id = unicode(self.test_group_project.scope_ids.usage_id)

        self.test_group_name = str(uuid.uuid4())
        self.test_group = Group.objects.create(
            name=self.test_group_name
        )
        GroupProfile.objects.create(
            name=self.test_group_name,
            group_id=self.test_group.id,
            group_type="series"
        )

        self.test_project = Project.objects.create(
            course_id=self.test_course_id,
            content_id=self.test_course_content_id
        )

        self.test_project2 = Project.objects.create(
            course_id=self.test_course_id,
            content_id=unicode(self.test_group_project.scope_ids.usage_id)
        )

        self.test_user_email = str(uuid.uuid4())
        self.test_user_username = str(uuid.uuid4())
        self.test_user = User.objects.create(
            email=self.test_user_email,
            username=self.test_user_username
        )

        self.test_user_email2 = str(uuid.uuid4())
        self.test_user_username2 = str(uuid.uuid4())
        self.test_user2 = User.objects.create(
            email=self.test_user_email2,
            username=self.test_user_username2
        )

        self.client = SecureClient()
        cache.clear()

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        json_data = json.dumps(data)

        response = self.client.post(
            uri, headers=headers, content_type='application/json', data=json_data)
        return response

    def do_get(self, uri):
        """Submit an HTTP GET request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.get(uri, headers=headers)
        return response

    def do_delete(self, uri):
        """Submit an HTTP DELETE request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.delete(uri, headers=headers)
        return response

    def do_delete_with_data(self, uri, data):
        """Submit an HTTP DELETE request with payload """
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.delete_with_data(uri, data, headers=headers)
        return response

    def test_workgroups_list_post(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = '{}{}{}/'.format(
            self.test_server_prefix,
            self.test_workgroups_uri,
            str(response.data['id'])
        )
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['name'], self.test_workgroup_name)
        self.assertEqual(response.data['project'], self.test_project.id)
        self.assertIsNotNone(response.data['users'])
        self.assertIsNotNone(response.data['groups'])
        self.assertIsNotNone(response.data['submissions'])
        self.assertIsNotNone(response.data['workgroup_reviews'])
        self.assertIsNotNone(response.data['peer_reviews'])
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

        # make sure a discussion cohort was created
        cohort_name = Workgroup.cohort_name_for_workgroup(
            self.test_project.id,
            response.data['id'],
            self.test_workgroup_name
        )
        cohort = get_cohort_by_name(self.test_course.id, cohort_name, CourseUserGroup.WORKGROUP)
        self.assertIsNotNone(cohort)

    def test_workgroups_detail_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['name'], self.test_workgroup_name)
        self.assertEqual(response.data['project'], self.test_project.id)
        self.assertIsNotNone(response.data['users'])
        self.assertIsNotNone(response.data['groups'])
        self.assertIsNotNone(response.data['submissions'])
        self.assertIsNotNone(response.data['workgroup_reviews'])
        self.assertIsNotNone(response.data['peer_reviews'])
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_workgroups_groups_post(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        groups_uri = '{}groups/'.format(test_uri)
        data = {"id": self.test_group.id}
        response = self.do_post(groups_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['groups'][0]['id'], self.test_group.id)
        self.assertEqual(response.data['groups'][0]['name'], self.test_group.name)

        test_groupnoprofile_name = str(uuid.uuid4())
        test_groupnoprofile = Group.objects.create(
            name=test_groupnoprofile_name
        )
        data = {"id": test_groupnoprofile.id}
        response = self.do_post(groups_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['groups'][1]['id'], test_groupnoprofile.id)
        self.assertEqual(response.data['groups'][1]['name'], test_groupnoprofile_name)

    def test_workgroups_groups_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        groups_uri = '{}groups/'.format(test_uri)
        data = {"id": self.test_group.id}
        response = self.do_post(groups_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(groups_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], self.test_group.id)
        self.assertEqual(response.data[0]['name'], self.test_group.name)

    def test_workgroups_users_post(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['users'][0]['id'], self.test_user.id)

        # make sure a discussion cohort was created
        cohort_name = Workgroup.cohort_name_for_workgroup(
            self.test_project.id,
            response.data['id'],
            self.test_workgroup_name
        )
        cohort = get_cohort_by_name(self.test_course.id, cohort_name, CourseUserGroup.WORKGROUP)
        self.assertIsNotNone(cohort)
        self.assertTrue(is_user_in_cohort(cohort, self.test_user.id, CourseUserGroup.WORKGROUP))


    def test_workgroups_users_post_preexisting_workgroup(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        data = {
            'name': "Workgroup 2",
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_workgroups_users_post_preexisting_project(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)

        # Second project created in setUp, adding a new workgroup
        data = {
            'name': "Workgroup 2",
            'project': self.test_project2.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)

        # Assign the test user to the alternate project/workgroup
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 400)


    def test_workgroups_users_post_with_cohort_backfill(self):
        """
        This test asserts a case where a workgroup was created before the existence of a cohorted discussion
        """
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['users'][0]['id'], self.test_user.id)

        cohort_name = Workgroup.cohort_name_for_workgroup(
            self.test_project.id,
            response.data['id'],
            self.test_workgroup_name
        )

        # now let's remove existing cohort users
        cohort = get_cohort_by_name(self.test_course.id, cohort_name, CourseUserGroup.WORKGROUP)
        self.assertTrue(is_user_in_cohort(cohort, self.test_user.id, CourseUserGroup.WORKGROUP))

        remove_user_from_cohort(cohort, self.test_user.username, CourseUserGroup.WORKGROUP)
        self.assertFalse(is_user_in_cohort(cohort, self.test_user.id, CourseUserGroup.WORKGROUP))

        # delete cohort
        delete_empty_cohort(self.test_course.id, cohort_name, CourseUserGroup.WORKGROUP)
        self.assertEqual(0, len(get_course_cohort_names(self.test_course.id, CourseUserGroup.WORKGROUP)))

        # add a 2nd user and make sure a discussion cohort was created and users were backfilled
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user2.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)

        # now inspect cohort and assert that things are as we anticipate (i.e. both users are in there)
        cohort = get_cohort_by_name(self.test_course.id, cohort_name, CourseUserGroup.WORKGROUP)
        self.assertIsNotNone(cohort)
        self.assertTrue(is_user_in_cohort(cohort, self.test_user.id, CourseUserGroup.WORKGROUP))
        self.assertTrue(is_user_in_cohort(cohort, self.test_user2.id, CourseUserGroup.WORKGROUP))

    def test_workgroups_users_delete(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_workgroup_uri = response.data['url']
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        # test if workgroup has exactly one user
        response = self.do_get(test_workgroup_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['users']), 1)

        # test to delete a user from workgroup
        data = {"id": self.test_user.id}
        response = self.do_delete_with_data(users_uri, data)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_workgroup_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['users']), 0)

        # test to delete an invalide user from workgroup
        data = {"id": '345345344'}
        response = self.do_delete_with_data(users_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_workgroups_users_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(users_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], self.test_user.id)
        self.assertEqual(response.data[0]['username'], self.test_user.username)
        self.assertEqual(response.data[0]['email'], self.test_user.email)

    def test_workgroups_peer_reviews_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        workgroup_id = response.data['id']
        pr_data = {
            'workgroup': workgroup_id,
            'user': self.test_user.id,
            'reviewer': self.test_user.username,
            'question': 'Test question?',
            'answer': 'Test answer!',
            'content_id': self.test_course_content_id
        }
        response = self.do_post(self.test_peer_reviews_uri, pr_data)
        self.assertEqual(response.status_code, 201)
        pr1_id = response.data['id']
        pr_data = {
            'workgroup': workgroup_id,
            'user': self.test_user.id,
            'reviewer': self.test_user.username,
            'question': 'Test question2',
            'answer': 'Test answer2',
            'content_id': self.test_course_id
        }
        response = self.do_post(self.test_peer_reviews_uri, pr_data)
        self.assertEqual(response.status_code, 201)
        pr2_id = response.data['id']

        test_uri = '{}{}/'.format(self.test_workgroups_uri, workgroup_id)
        peer_reviews_uri = '{}peer_reviews/'.format(test_uri)
        response = self.do_get(peer_reviews_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], pr1_id)
        self.assertEqual(response.data[0]['reviewer'], self.test_user.username)

        content_id = {"content_id": self.test_course_content_id}
        test_uri = '{}{}/peer_reviews/?{}'.format(self.test_workgroups_uri, workgroup_id, urlencode(content_id))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], pr1_id)
        self.assertEqual(response.data[0]['reviewer'], self.test_user.username)


    def test_workgroups_workgroup_reviews_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        workgroup_id = response.data['id']
        wr_data = {
            'workgroup': workgroup_id,
            'reviewer': self.test_user.username,
            'question': 'Test question?',
            'answer': 'Test answer!',
            'content_id': self.test_course_content_id
        }
        response = self.do_post(self.test_workgroup_reviews_uri, wr_data)
        self.assertEqual(response.status_code, 201)
        wr1_id = response.data['id']
        wr_data = {
            'workgroup': workgroup_id,
            'reviewer': self.test_user.username,
            'question': 'Test question?',
            'answer': 'Test answer!',
            'content_id': self.test_course_id
        }
        response = self.do_post(self.test_workgroup_reviews_uri, wr_data)
        self.assertEqual(response.status_code, 201)

        test_uri = '{}{}/'.format(self.test_workgroups_uri, workgroup_id)
        workgroup_reviews_uri = '{}workgroup_reviews/'.format(test_uri)
        response = self.do_get(workgroup_reviews_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], wr1_id)
        self.assertEqual(response.data[0]['reviewer'], self.test_user.username)

        content_id = {"content_id": self.test_course_content_id}
        test_uri = '{}{}/workgroup_reviews/?{}'.format(self.test_workgroups_uri, workgroup_id, urlencode(content_id))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], wr1_id)
        self.assertEqual(response.data[0]['reviewer'], self.test_user.username)

    def test_workgroups_submissions_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        workgroup_id = response.data['id']
        data = {
            'workgroup': workgroup_id,
            'user': self.test_user.id,
            'document_id': 'filename.pdf',
            'document_url': 'https://s3.amazonaws.com/bucketname/filename.pdf',
            'document_mime_type': 'application/pdf'
        }
        response = self.do_post(self.test_submissions_uri, data)
        self.assertEqual(response.status_code, 201)
        submission_id = response.data['id']
        test_uri = '{}{}/'.format(self.test_workgroups_uri, workgroup_id)
        submissions_uri = '{}submissions/'.format(test_uri)
        response = self.do_get(submissions_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], submission_id)
        self.assertEqual(response.data[0]['user'], self.test_user.id)

    def test_workgroups_grades_post(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        workgroup_id = response.data['id']
        users_uri = '{}{}/users/'.format(self.test_workgroups_uri, workgroup_id)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        data = {"id": self.test_user2.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)

        grade_data = {
            'course_id': self.test_course_id,
            'content_id': self.test_course_content_id,
            'grade': 0.85,
            'max_grade': 0.75,
        }
        grades_uri = '{}{}/grades/'.format(self.test_workgroups_uri, workgroup_id)
        response = self.do_post(grades_uri, grade_data)
        self.assertEqual(response.status_code, 201)

        # Confirm the grades for the users
        course_grades_uri = '{}/{}/metrics/grades/'.format(self.test_courses_uri, self.test_course_id)
        response = self.do_get(course_grades_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['grades']), 0)

    def test_workgroups_grades_post_invalid_course(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        workgroup_id = response.data['id']
        users_uri = '{}{}/users/'.format(self.test_workgroups_uri, workgroup_id)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        data = {"id": self.test_user2.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)

        grade_data = {
            'course_id': self.test_bogus_course_id,
            'content_id': self.test_course_content_id,
            'grade': 0.85,
            'max_grade': 0.75,
        }
        grades_uri = '{}{}/grades/'.format(self.test_workgroups_uri, workgroup_id)
        response = self.do_post(grades_uri, grade_data)
        self.assertEqual(response.status_code, 400)

        grade_data = {
            'course_id': "really-invalid-course-id",
            'content_id': self.test_course_content_id,
            'grade': 0.85,
            'max_grade': 0.75,
        }
        grades_uri = '{}{}/grades/'.format(self.test_workgroups_uri, workgroup_id)
        response = self.do_post(grades_uri, grade_data)
        self.assertEqual(response.status_code, 400)

    def test_workgroups_grades_post_invalid_course_content(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        workgroup_id = response.data['id']
        users_uri = '{}{}/users/'.format(self.test_workgroups_uri, workgroup_id)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        data = {"id": self.test_user2.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)

        grade_data = {
            'course_id': self.test_course_id,
            'content_id': self.test_bogus_course_content_id,
            'grade': 0.85,
            'max_grade': 0.75,
        }
        grades_uri = '{}{}/grades/'.format(self.test_workgroups_uri, workgroup_id)
        response = self.do_post(grades_uri, grade_data)
        self.assertEqual(response.status_code, 400)

    def test_workgroups_grades_post_invalid_requests(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        workgroup_id = response.data['id']

        users_uri = '{}{}/users/'.format(self.test_workgroups_uri, workgroup_id)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        data = {"id": self.test_user2.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)

        grades_uri = '{}{}/grades/'.format(self.test_workgroups_uri, workgroup_id)
        grade_data = {
            'content_id': self.test_course_content_id,
            'grade': 0.85,
            'max_grade': 0.75,
        }
        response = self.do_post(grades_uri, grade_data)
        self.assertEqual(response.status_code, 400)

        grade_data = {
            'course_id': self.test_bogus_course_id,
            'content_id': self.test_course_content_id,
            'grade': 0.85,
            'max_grade': 0.75,
        }
        response = self.do_post(grades_uri, grade_data)
        self.assertEqual(response.status_code, 400)

        grade_data = {
            'course_id': self.test_course_id,
            'grade': 0.85,
            'max_grade': 0.75,
        }
        response = self.do_post(grades_uri, grade_data)
        self.assertEqual(response.status_code, 400)

        grade_data = {
            'course_id': self.test_course_id,
            'content_id': self.test_course_content_id,
            'max_grade': 0.75,
        }
        response = self.do_post(grades_uri, grade_data)
        self.assertEqual(response.status_code, 400)

        grade_data = {
            'course_id': self.test_course_id,
            'content_id': self.test_course_content_id,
            'grade': 0.85,
        }
        response = self.do_post(grades_uri, grade_data)
        self.assertEqual(response.status_code, 400)

    def test_submissions_list_post_invalid_relationships(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))

        users_uri = '{}users/'.format(test_uri)
        data = {"id": 123456}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 400)

        groups_uri = '{}groups/'.format(test_uri)
        data = {"id": 123456}
        response = self.do_post(groups_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_workgroups_detail_get_undefined(self):
        test_uri = '{}123456789/'.format(self.test_workgroups_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_workgroups_detail_delete(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
