"""
Tests for Cohort API
"""
import json
import tempfile

import ddt
from django.core.urlresolvers import reverse
from edx_oauth2_provider.tests.factories import AccessTokenFactory, ClientFactory
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory

from openedx.core.djangolib.testing.utils import skip_unless_lms
from .. import cohorts

USERNAME = 'honor'
USER_MAIL = 'honor@example.com'
SETTINGS_PAYLOAD = '{"is_cohorted": true}'
HANDLER_POST_PAYLOAD = '{"name":"Default","user_count":0,"assignment_type":"random","user_partition_id":null\
,"group_id":null}'
HANDLER_PATCH_PAYLOAD = '{"name":"Default Group","group_id":null,"user_partition_id":null,"assignment_type":"random"}'
ADD_USER_PAYLOAD = json.dumps({'users': [USER_MAIL, ]})
CSV_DATA = '''email,cohort\n{},DEFAULT'''.format(USER_MAIL)


@skip_unless_lms
@ddt.ddt
class TestCohortOauth(SharedModuleStoreTestCase):
    """
    Tests for cohort API oauth authentication
    """

    password = 'password'

    @classmethod
    def setUpClass(cls):
        super(TestCohortOauth, cls).setUpClass()
        cls.user = UserFactory(username=USERNAME, email=USER_MAIL, password=cls.password)
        cls.staff_user = UserFactory(is_staff=True, password=cls.password)
        cls.course_key = ToyCourseFactory.create().id
        cls.course_str = unicode(cls.course_key)

    @ddt.data({'path_name': 'api_cohorts:cohort_settings'},
              {'path_name': 'api_cohorts:cohort_handler'}, )
    @ddt.unpack
    def test_oauth_list(self, path_name):
        """ Verify the endpoints supports OAuth, and only allows authorization for staff users. """
        path = reverse(path_name, kwargs={'course_key_string': self.course_str})
        user = UserFactory(is_staff=False)
        oauth_client = ClientFactory.create()
        access_token = AccessTokenFactory.create(user=user, client=oauth_client).token
        headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + access_token
        }

        # Non-staff users should not have access to the API
        response = self.client.get(path=path, **headers)
        self.assertEqual(response.status_code, 403)

        # Staff users should have access to the API
        user.is_staff = True
        user.save()
        response = self.client.get(path=path, **headers)
        self.assertEqual(response.status_code, 200)

    def test_oauth_users(self):
        """ Verify the endpoint supports OAuth, and only allows authorization for staff users. """
        cohorts.add_cohort(self.course_key, "DEFAULT", "random")
        path = reverse('api_cohorts:cohort_users', kwargs={'course_key_string': self.course_str, 'cohort_id': 1})
        user = UserFactory(is_staff=False)
        oauth_client = ClientFactory.create()
        access_token = AccessTokenFactory.create(user=user, client=oauth_client).token
        headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + access_token
        }
        data = {
            'users': [user.username]
        }

        # Non-staff users should not have access to the API
        response = self.client.post(path=path, data=data, **headers)
        self.assertEqual(response.status_code, 403)

        # Staff users should have access to the API
        user.is_staff = True
        user.save()
        response = self.client.post(path=path, data=data, **headers)
        self.assertEqual(response.status_code, 200)

    def test_oauth_csv(self):
        """ Verify the endpoint supports OAuth, and only allows authorization for staff users. """
        cohorts.add_cohort(self.course_key, "DEFAULT", "random")
        path = reverse('api_cohorts:cohort_users_csv', kwargs={'course_key_string': self.course_str})
        user = UserFactory(is_staff=False)
        oauth_client = ClientFactory.create()
        access_token = AccessTokenFactory.create(user=user, client=oauth_client).token
        headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + access_token
        }

        # Non-staff users should not have access to the API
        response = self.client.post(path=path, **headers)
        self.assertEqual(response.status_code, 403)

        # Staff users should have access to the API
        user.is_staff = True
        user.save()
        response = self.client.post(path=path, **headers)
        self.assertEqual(response.status_code, 400)


@skip_unless_lms
@ddt.ddt
class TestCohortApi(SharedModuleStoreTestCase):
    """
    Tests for cohort API endpoints
    """

    password = 'password'

    @classmethod
    def setUpClass(cls):
        super(TestCohortApi, cls).setUpClass()
        cls.user = UserFactory(username=USERNAME, email=USER_MAIL, password=cls.password)
        cls.staff_user = UserFactory(is_staff=True, password=cls.password)
        cls.course_key = ToyCourseFactory.create().id
        cls.course_str = unicode(cls.course_key)

    @ddt.data({'is_staff': True, 'payload': '', 'status': 200},
              {'is_staff': False, 'payload': '', 'status': 403},
              {'is_staff': True, 'payload': SETTINGS_PAYLOAD, 'status': 200},
              {'is_staff': False, 'payload': SETTINGS_PAYLOAD, 'status': 403})
    @ddt.unpack
    def test_cohort_settings(self, is_staff, payload, status):
        """
        Test GET and PUT methods of cohort settings endpoint
        """
        path = reverse('api_cohorts:cohort_settings', kwargs={'course_key_string': self.course_str})
        user = self.staff_user if is_staff else self.user
        assert self.client.login(username=user.username, password=self.password)
        if payload:
            response = self.client.put(
                path=path,
                data=payload,
                content_type='application/json')
        else:
            response = self.client.get(path=path)
        assert response.status_code == status

    @ddt.data({'is_staff': False, 'payload': HANDLER_POST_PAYLOAD, 'status': 403},
              {'is_staff': True, 'payload': HANDLER_POST_PAYLOAD, 'status': 200},
              {'is_staff': False, 'payload': '', 'status': 403},
              {'is_staff': True, 'payload': '', 'status': 200}, )
    @ddt.unpack
    def test_cohort_handler(self, is_staff, payload, status):
        """
        Test GET and POST methods of cohort handler endpoint
        """
        path = reverse('api_cohorts:cohort_handler', kwargs={'course_key_string': self.course_str})
        user = self.staff_user if is_staff else self.user
        assert self.client.login(username=user.username, password=self.password)
        if payload:
            response = self.client.post(
                path=path,
                data=payload,
                content_type='application/json')
        else:
            response = self.client.get(path=path)
        assert response.status_code == status

    @ddt.data({'is_staff': False, 'payload': HANDLER_PATCH_PAYLOAD, 'status': 403},
              {'is_staff': True, 'payload': HANDLER_PATCH_PAYLOAD, 'status': 204},
              {'is_staff': False, 'payload': '', 'status': 403},
              {'is_staff': True, 'payload': '', 'status': 200}, )
    @ddt.unpack
    def test_cohort_handler_patch(self, is_staff, payload, status):
        """
        Test GET and PATCH methods of cohort handler endpoint for a specific cohort
        """
        cohorts.add_cohort(self.course_key, "DEFAULT", "random")
        cohort_id = 1
        path = reverse('api_cohorts:cohort_handler',
                       kwargs={'course_key_string': self.course_str, 'cohort_id': cohort_id})
        user = self.staff_user if is_staff else self.user
        assert self.client.login(username=user.username, password=self.password)
        if payload:
            response = self.client.patch(
                path=path,
                data=payload,
                content_type='application/json')
        else:
            response = self.client.get(path=path)
        assert response.status_code == status

    @ddt.data({'is_staff': False, 'payload': ADD_USER_PAYLOAD, 'status': 403},
              {'is_staff': True, 'payload': ADD_USER_PAYLOAD, 'status': 200}, )
    @ddt.unpack
    def test_add_users_to_cohort(self, is_staff, payload, status):
        """
        Test POST method for adding users to a cohort
        """
        cohorts.add_cohort(self.course_key, "DEFAULT", "random")
        cohort_id = 1
        path = reverse('api_cohorts:cohort_users',
                       kwargs={'course_key_string': self.course_str, 'cohort_id': cohort_id})
        user = self.staff_user if is_staff else self.user
        assert self.client.login(username=user.username, password=self.password)
        response = self.client.post(
            path=path,
            data=payload,
            content_type='application/json')
        assert response.status_code == status

    @ddt.data({'is_staff': False, 'username': USERNAME, 'status': 403},
              {'is_staff': True, 'username': USERNAME, 'status': 204},
              {'is_staff': True, 'username': 'doesnotexist', 'status': 404},
              {'is_staff': False, 'username': None, 'status': 403},
              {'is_staff': True, 'username': None, 'status': 404}, )
    @ddt.unpack
    def test_remove_user_from_cohort(self, is_staff, username, status):
        """
        Test DELETE method for removing an user from a cohort.
        """
        cohort = cohorts.add_cohort(self.course_key, "DEFAULT", "random")
        cohorts.add_user_to_cohort(cohort, USERNAME)
        cohort_id = 1
        path = reverse('api_cohorts:cohort_users',
                       kwargs={'course_key_string': self.course_str, 'cohort_id': cohort_id, 'username': username})
        user = self.staff_user if is_staff else self.user
        assert self.client.login(username=user.username, password=self.password)
        response = self.client.delete(path=path)
        assert response.status_code == status

    @ddt.data({'is_staff': False, 'payload': CSV_DATA, 'status': 403},
              {'is_staff': True, 'payload': CSV_DATA, 'status': 204},
              {'is_staff': True, 'payload': '', 'status': 400},
              {'is_staff': False, 'payload': '', 'status': 403}, )
    @ddt.unpack
    def test_add_users_csv(self, is_staff, payload, status):
        """
        Test adding users to cohorts using a CSV file
        """
        cohorts.add_cohort(self.course_key, "DEFAULT", "random")
        # this temporary file will be removed in `self.tearDown()`
        __, file_name = tempfile.mkstemp(suffix='.csv', dir=tempfile.mkdtemp())
        with open(file_name, 'w') as file_pointer:
            file_pointer.write(payload.encode('utf-8'))
        path = reverse('api_cohorts:cohort_users_csv', kwargs={'course_key_string': self.course_str})
        user = self.staff_user if is_staff else self.user
        assert self.client.login(username=user.username, password=self.password)
        with open(file_name, 'r') as file_pointer:
            response = self.client.post(path=path,
                                        data={'uploaded-file': file_pointer})
            assert response.status_code == status
