import datetime

import pytz
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from opaque_keys.edx.keys import CourseKey
from rest_framework.test import APIClient
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ToyCourseFactory

from openedx.core.lib.courses import course_image_url
from student.models import CourseAccessRole
from student.tests.factories import AdminFactory, TEST_PASSWORD, UserFactory
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

    def assert_access_role(self, course_run, user, role):
        # An error will be raised if the endpoint did not create the role
        CourseAccessRole.objects.get(course_id=course_run.id, user=user, role=role)

    def assert_course_access_role_count(self, course_run, expected):
        assert CourseAccessRole.objects.filter(course_id=course_run.id).count() == expected

    def get_serializer_context(self):
        return {'request': RequestFactory().get('')}

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
        actual = sorted(response.data['results'], key=lambda course_run: course_run['id'])
        assert actual == CourseRunSerializer(course_runs, many=True, context=self.get_serializer_context()).data

    def test_retrieve(self):
        course_run = CourseFactory()
        url = reverse('api:v1:course_run-detail', kwargs={'pk': str(course_run.id)})
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data == CourseRunSerializer(course_run, context=self.get_serializer_context()).data

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
        self.assert_access_role(course_run, user, role)
        self.assert_course_access_role_count(course_run, 1)

        course_run = modulestore().get_course(course_run.id)
        assert response.data == CourseRunSerializer(course_run, context=self.get_serializer_context()).data
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
        role = 'staff'
        start = datetime.datetime.now(pytz.UTC).replace(microsecond=0)
        course_run = CourseFactory(start=start, end=None, enrollment_start=None, enrollment_end=None)

        # The request should only update or create new team members
        existing_user = UserFactory()
        CourseAccessRole.objects.create(course_id=course_run.id, role=role, user=existing_user)
        new_user = UserFactory()
        CourseAccessRole.objects.create(course_id=course_run.id, role=role, user=new_user)
        assert CourseAccessRole.objects.filter(course_id=course_run.id).count() == 2

        data = {
            'team': [
                {
                    'user': existing_user.username,
                    'role': role,
                },
                {
                    'user': new_user.username,
                    'role': role,
                },
            ],
        }

        url = reverse('api:v1:course_run-detail', kwargs={'pk': str(course_run.id)})
        response = self.client.patch(url, data, format='json')
        assert response.status_code == 200
        self.assert_access_role(course_run, existing_user, role)
        self.assert_access_role(course_run, new_user, role)
        self.assert_course_access_role_count(course_run, 2)

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
        self.assert_access_role(course_run, user, role)
        self.assert_course_access_role_count(course_run, 1)

    def test_images_upload(self):
        # http://www.django-rest-framework.org/api-guide/parsers/#fileuploadparser
        course_run = CourseFactory()
        expected_filename = 'course_image.png'
        content_key = StaticContent.compute_location(course_run.id, expected_filename)

        assert course_run.course_image != expected_filename

        try:
            contentstore().find(content_key)
            self.fail('No image should be associated with a new course run.')
        except NotFoundError:
            pass

        url = reverse('api:v1:course_run-images', kwargs={'pk': str(course_run.id)})
        # PNG. Single black pixel
        content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS' \
                  b'\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'

        # We are intentionally passing the incorrect JPEG extension here
        upload = SimpleUploadedFile('card_image.jpg', content, content_type='image/png')
        response = self.client.post(url, {'card_image': upload}, format='multipart')
        assert response.status_code == 200

        course_run = modulestore().get_course(course_run.id)
        assert course_run.course_image == expected_filename

        expected = {'card_image': RequestFactory().get('').build_absolute_uri(course_image_url(course_run))}
        assert response.data == expected

        # There should now be an image stored
        contentstore().find(content_key)

    def test_rerun(self):
        course_run = ToyCourseFactory()
        start = datetime.datetime.now(pytz.UTC).replace(microsecond=0)
        end = start + datetime.timedelta(days=30)
        user = UserFactory()
        role = 'instructor'
        run = '3T2017'
        url = reverse('api:v1:course_run-rerun', kwargs={'pk': str(course_run.id)})
        data = {
            'run': run,
            'schedule': {
                'start': serialize_datetime(start),
                'end': serialize_datetime(end),
                'enrollment_start': None,
                'enrollment_end': None,
            },
            'team': [
                {
                    'user': user.username,
                    'role': role,
                }
            ],
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == 201

        course_run_key = CourseKey.from_string(response.data['id'])
        course_run = modulestore().get_course(course_run_key)
        assert course_run.id.run == run
        self.assert_course_run_schedule(course_run, start, end, None, None)
        self.assert_access_role(course_run, user, role)
        self.assert_course_access_role_count(course_run, 1)

    def test_rerun_duplicate_run(self):
        course_run = ToyCourseFactory()
        url = reverse('api:v1:course_run-rerun', kwargs={'pk': str(course_run.id)})
        data = {
            'run': course_run.id.run,
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == 400
        assert response.data == {'run': ['Course run {key} already exists'.format(key=course_run.id)]}
