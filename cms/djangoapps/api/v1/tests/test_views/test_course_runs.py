import datetime

import pytz
from django.core.urlresolvers import reverse
from opaque_keys.edx.keys import CourseKey
from rest_framework.test import APIClient

from student.models import CourseAccessRole
from student.tests.factories import AdminFactory, TEST_PASSWORD, UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from ..utils import serialize_datetime
from ...serializers.course_runs import CourseRunSerializer


class CourseRunViewSetTests(ModuleStoreTestCase):
    list_url = reverse('api:v1:course_run-list')

    def setUp(self):
        super(CourseRunViewSetTests, self).setUp()
        self.client = APIClient()
        user = AdminFactory()
        self.client.login(username=user.username, password=TEST_PASSWORD)

    def assert_course_run_schedule(self, course_run, start, end, enrollment_start, enrollment_end):
        assert course_run.start == start
        assert course_run.end == end
        assert course_run.enrollment_start == enrollment_start
        assert course_run.enrollment_end == enrollment_end

    def test_without_authentication(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        assert response.status_code == 401

    def test_without_authorization(self):
        user = UserFactory(is_staff=False)
        self.client.login(username=user.username, password=TEST_PASSWORD)
        response = self.client.get(self.list_url)
        assert response.status_code == 403

    def test_list(self):
        course_runs = CourseFactory.create_batch(3)
        response = self.client.get(self.list_url)
        assert response.status_code == 200

        # Order matters for the assertion
        course_runs = sorted(course_runs, key=lambda course_run: str(course_run.id))
        actual = sorted(response.data, key=lambda course_run: course_run['id'])
        assert actual == CourseRunSerializer(course_runs, many=True).data

    def test_retrieve(self):
        course_run = CourseFactory()
        url = reverse('api:v1:course_run-detail', kwargs={'pk': str(course_run.id)})
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data == CourseRunSerializer(course_run).data

    def test_retrieve_not_found(self):
        url = reverse('api:v1:course_run-detail', kwargs={'pk': 'course-v1:TestX+Test101x+1T2017'})
        response = self.client.get(url)
        assert response.status_code == 404

    def test_update_not_found(self):
        url = reverse('api:v1:course_run-detail', kwargs={'pk': 'course-v1:TestX+Test101x+1T2017'})
        response = self.client.put(url, {})
        assert response.status_code == 404

    def test_update(self):
        course_run = CourseFactory(start=None, end=None, enrollment_start=None, enrollment_end=None)
        assert CourseAccessRole.objects.filter(course_id=course_run.id).count() == 0

        url = reverse('api:v1:course_run-detail', kwargs={'pk': str(course_run.id)})
        start = datetime.datetime.now(pytz.UTC).replace(microsecond=0)
        end = start + datetime.timedelta(days=30)
        enrollment_start = start - datetime.timedelta(days=7)
        enrollment_end = end - datetime.timedelta(days=14)
        title = 'A New Testing Strategy'
        user = UserFactory()
        role = 'staff'
        data = {
            'title': title,
            'schedule': {
                'start': serialize_datetime(start),
                'end': serialize_datetime(end),
                'enrollment_start': serialize_datetime(enrollment_start),
                'enrollment_end': serialize_datetime(enrollment_end),
            },
            'team': [
                {
                    'user': user.username,
                    'role': role,
                }
            ],
        }
        response = self.client.put(url, data, format='json')
        assert response.status_code == 200

        # An error will be raised if the endpoint doesn't create the role
        CourseAccessRole.objects.get(course_id=course_run.id, user=user, role=role)
        assert CourseAccessRole.objects.filter(course_id=course_run.id).count() == 1

        course_run = modulestore().get_course(course_run.id)
        assert response.data == CourseRunSerializer(course_run).data
        assert course_run.display_name == title
        self.assert_course_run_schedule(course_run, start, end, enrollment_start, enrollment_end)

    def test_update_with_invalid_user(self):
        course_run = CourseFactory()
        url = reverse('api:v1:course_run-detail', kwargs={'pk': str(course_run.id)})
        data = {
            'title': course_run.display_name,
            'team': [
                {
                    'user': 'test-user',
                    'role': 'staff',
                }
            ]
        }
        response = self.client.put(url, data, format='json')
        assert response.status_code == 400
        assert response.data == {'team': [{'user': ['Object with username=test-user does not exist.']}]}

    def test_partial_update(self):
        start = datetime.datetime.now(pytz.UTC).replace(microsecond=0)
        course_run = CourseFactory(start=start, end=None, enrollment_start=None, enrollment_end=None)
        assert CourseAccessRole.objects.filter(course_id=course_run.id).count() == 0

        user = UserFactory()
        role = 'staff'
        data = {
            'team': [
                {
                    'user': user.username,
                    'role': role,
                }
            ],
        }

        url = reverse('api:v1:course_run-detail', kwargs={'pk': str(course_run.id)})
        response = self.client.patch(url, data, format='json')
        assert response.status_code == 200

        # An error will be raised if the endpoint doesn't create the role
        CourseAccessRole.objects.get(course_id=course_run.id, user=user, role=role)
        assert CourseAccessRole.objects.filter(course_id=course_run.id).count() == 1

        course_run = modulestore().get_course(course_run.id)
        self.assert_course_run_schedule(course_run, start, None, None, None)

    def test_create(self):
        start = datetime.datetime.now(pytz.UTC).replace(microsecond=0)
        end = start + datetime.timedelta(days=30)
        enrollment_start = start - datetime.timedelta(days=7)
        enrollment_end = end - datetime.timedelta(days=14)
        user = UserFactory()
        role = 'staff'
        data = {
            'title': 'Testing 101',
            'org': 'TestingX',
            'number': 'Testing101x',
            'run': '3T2017',
            'schedule': {
                'start': serialize_datetime(start),
                'end': serialize_datetime(end),
                'enrollment_start': serialize_datetime(enrollment_start),
                'enrollment_end': serialize_datetime(enrollment_end),
            },
            'team': [
                {
                    'user': user.username,
                    'role': role,
                }
            ],
        }
        response = self.client.post(self.list_url, data, format='json')
        assert response.status_code == 201

        course_run_key = CourseKey.from_string(response.data['id'])
        course_run = modulestore().get_course(course_run_key)
        assert course_run.display_name == data['title']
        assert course_run.id.org == data['org']
        assert course_run.id.course == data['number']
        assert course_run.id.run == data['run']
        self.assert_course_run_schedule(course_run, start, end, enrollment_start, enrollment_end)

        # An error will be raised if the endpoint doesn't create the role
        CourseAccessRole.objects.get(course_id=course_run.id, user=user, role=role)
        assert CourseAccessRole.objects.filter(course_id=course_run.id).count() == 1
