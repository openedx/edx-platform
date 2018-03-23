import json
import logging
import unittest
import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.timezone import now

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from mock import patch
from opaque_keys.edx.locator import CourseKey
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from student.models import CourseEnrollment
from student.tests.factories import (TEST_PASSWORD, CourseEnrollmentFactory, UserFactory)

log = logging.getLogger(__name__)

# Entitlements is not in CMS' INSTALLED_APPS so these imports will error during test collection
if settings.ROOT_URLCONF == 'lms.urls':
    from entitlements.tests.factories import CourseEntitlementFactory
    from entitlements.models import CourseEntitlement
    from entitlements.api.v1.serializers import CourseEntitlementSerializer


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EntitlementViewSetTest(ModuleStoreTestCase):
    ENTITLEMENTS_DETAILS_PATH = 'entitlements_api:v1:entitlements-detail'

    def setUp(self):
        super(EntitlementViewSetTest, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.course = CourseFactory()
        self.course_mode = CourseModeFactory(
            course_id=self.course.id,
            mode_slug=CourseMode.VERIFIED,
            # This must be in the future to ensure it is returned by downstream code.
            expiration_datetime=now() + timedelta(days=1)
        )

        self.entitlements_list_url = reverse('entitlements_api:v1:entitlements-list')

    def _get_data_set(self, user, course_uuid):
        """
        Get a basic data set for an entitlement
        """
        return {
            "user": user.username,
            "mode": "verified",
            "course_uuid": course_uuid,
            "order_number": "EDX-1001",
        }

    def test_auth_required(self):
        self.client.logout()
        response = self.client.get(self.entitlements_list_url)
        assert response.status_code == 401

    def test_staff_user_not_required_for_get(self):
        not_staff_user = UserFactory()
        self.client.login(username=not_staff_user.username, password=TEST_PASSWORD)
        response = self.client.get(self.entitlements_list_url)
        assert response.status_code == 200

    def test_add_entitlement_with_missing_data(self):
        entitlement_data_missing_parts = self._get_data_set(self.user, str(uuid.uuid4()))
        entitlement_data_missing_parts.pop('mode')
        entitlement_data_missing_parts.pop('course_uuid')

        response = self.client.post(
            self.entitlements_list_url,
            data=json.dumps(entitlement_data_missing_parts),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_staff_user_required_for_post(self):
        not_staff_user = UserFactory()
        self.client.login(username=not_staff_user.username, password=TEST_PASSWORD)

        course_uuid = uuid.uuid4()
        entitlement_data = self._get_data_set(self.user, str(course_uuid))

        response = self.client.post(
            self.entitlements_list_url,
            data=json.dumps(entitlement_data),
            content_type='application/json',
        )
        assert response.status_code == 403

    def test_staff_user_required_for_delete(self):
        not_staff_user = UserFactory()
        self.client.login(username=not_staff_user.username, password=TEST_PASSWORD)

        course_entitlement = CourseEntitlementFactory.create()
        url = reverse(self.ENTITLEMENTS_DETAILS_PATH, args=[str(course_entitlement.uuid)])

        response = self.client.delete(
            url,
            content_type='application/json',
        )
        assert response.status_code == 403

    def test_add_entitlement(self):
        course_uuid = uuid.uuid4()
        entitlement_data = self._get_data_set(self.user, str(course_uuid))

        response = self.client.post(
            self.entitlements_list_url,
            data=json.dumps(entitlement_data),
            content_type='application/json',
        )
        assert response.status_code == 201
        results = response.data

        course_entitlement = CourseEntitlement.objects.get(
            user=self.user,
            course_uuid=course_uuid
        )
        assert results == CourseEntitlementSerializer(course_entitlement).data

    def test_add_entitlement_with_support_detail(self):
        """
        Verify that an EntitlementSupportDetail entry is made when the request includes support interaction information.
        """
        course_uuid = uuid.uuid4()
        entitlement_data = self._get_data_set(self.user, str(course_uuid))
        entitlement_data['support_details'] = [
            {
                "action": "CREATE",
                "comments": "Family emergency."
            },
        ]

        response = self.client.post(
            self.entitlements_list_url,
            data=json.dumps(entitlement_data),
            content_type='application/json',
        )
        assert response.status_code == 201
        results = response.data

        course_entitlement = CourseEntitlement.objects.get(
            user=self.user,
            course_uuid=course_uuid
        )
        assert results == CourseEntitlementSerializer(course_entitlement).data

    @patch("entitlements.api.v1.views.get_course_runs_for_course")
    def test_add_entitlement_and_upgrade_audit_enrollment(self, mock_get_course_runs):
        """
        Verify that if an entitlement is added for a user, if the user has one upgradeable enrollment
        that enrollment is upgraded to the mode of the entitlement and linked to the entitlement.
        """
        course_uuid = uuid.uuid4()
        entitlement_data = self._get_data_set(self.user, str(course_uuid))
        mock_get_course_runs.return_value = [{'key': str(self.course.id)}]

        # Add an audit course enrollment for user.
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode=CourseMode.AUDIT)

        response = self.client.post(
            self.entitlements_list_url,
            data=json.dumps(entitlement_data),
            content_type='application/json',
        )
        assert response.status_code == 201
        results = response.data

        course_entitlement = CourseEntitlement.objects.get(
            user=self.user,
            course_uuid=course_uuid
        )
        # Assert that enrollment mode is now verified
        enrollment_mode = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)[0]
        assert enrollment_mode == course_entitlement.mode
        assert course_entitlement.enrollment_course_run == enrollment
        assert results == CourseEntitlementSerializer(course_entitlement).data

    @patch("entitlements.api.v1.views.get_course_runs_for_course")
    def test_add_entitlement_inactive_audit_enrollment(self, mock_get_course_runs):
        """
        Verify that if an entitlement is added for a user, if the user has an inactive audit enrollment
        that enrollment is NOT upgraded to the mode of the entitlement and linked to the entitlement.
        """
        course_uuid = uuid.uuid4()
        entitlement_data = self._get_data_set(self.user, str(course_uuid))
        mock_get_course_runs.return_value = [{'key': str(self.course.id)}]

        # Add an audit course enrollment for user.
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode=CourseMode.AUDIT)
        enrollment.update_enrollment(is_active=False)
        response = self.client.post(
            self.entitlements_list_url,
            data=json.dumps(entitlement_data),
            content_type='application/json',
        )
        assert response.status_code == 201
        results = response.data

        course_entitlement = CourseEntitlement.objects.get(
            user=self.user,
            course_uuid=course_uuid
        )
        # Assert that enrollment mode is now verified
        enrollment_mode, enrollment_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        assert enrollment_mode == CourseMode.AUDIT
        assert enrollment_active is False
        assert course_entitlement.enrollment_course_run is None
        assert results == CourseEntitlementSerializer(course_entitlement).data

    def test_non_staff_get_select_entitlements(self):
        not_staff_user = UserFactory()
        self.client.login(username=not_staff_user.username, password=TEST_PASSWORD)
        CourseEntitlementFactory.create_batch(2)
        entitlement = CourseEntitlementFactory.create(user=not_staff_user)
        response = self.client.get(
            self.entitlements_list_url,
            content_type='application/json',
        )
        assert response.status_code == 200

        results = response.data.get('results', [])  # pylint: disable=no-member
        assert results == CourseEntitlementSerializer([entitlement], many=True).data

    def test_staff_get_only_staff_entitlements(self):
        CourseEntitlementFactory.create_batch(2)
        entitlement = CourseEntitlementFactory.create(user=self.user)

        response = self.client.get(
            self.entitlements_list_url,
            content_type='application/json',
        )
        assert response.status_code == 200

        results = response.data.get('results', [])
        assert results == CourseEntitlementSerializer([entitlement], many=True).data

    def test_staff_get_expired_entitlements(self):
        past_datetime = now() - timedelta(days=365 * 2)
        entitlements = CourseEntitlementFactory.create_batch(2, created=past_datetime, user=self.user)

        # Set the first entitlement to be at a time that it isn't expired
        entitlements[0].created = now()
        entitlements[0].save()

        response = self.client.get(
            self.entitlements_list_url,
            content_type='application/json',
        )
        assert response.status_code == 200
        results = response.data.get('results', [])  # pylint: disable=no-member
        # Make sure that the first result isn't expired, and the second one is also not for staff users
        assert results[0].get('expired_at') is None and results[1].get('expired_at') is None

    def test_get_user_expired_entitlements(self):
        past_datetime = now() - timedelta(days=365 * 2)
        not_staff_user = UserFactory()
        self.client.login(username=not_staff_user.username, password=TEST_PASSWORD)
        entitlement_user2 = CourseEntitlementFactory.create_batch(2, user=not_staff_user, created=past_datetime)
        url = reverse('entitlements_api:v1:entitlements-list')
        url += '?user={username}'.format(username=not_staff_user.username)

        # Set the first entitlement to be at a time that it isn't expired
        entitlement_user2[0].created = now()
        entitlement_user2[0].save()

        response = self.client.get(
            url,
            content_type='application/json',
        )
        assert response.status_code == 200

        results = response.data.get('results', [])  # pylint: disable=no-member
        assert results[0].get('expired_at') is None and results[1].get('expired_at')

    def test_get_user_entitlements(self):
        user2 = UserFactory()
        CourseEntitlementFactory.create()
        entitlement_user2 = CourseEntitlementFactory.create(user=user2)
        url = reverse('entitlements_api:v1:entitlements-list')
        url += '?user={username}'.format(username=user2.username)
        response = self.client.get(
            url,
            content_type='application/json',
        )
        assert response.status_code == 200

        results = response.data.get('results', [])
        assert results == CourseEntitlementSerializer([entitlement_user2], many=True).data

    def test_get_entitlement_by_uuid(self):
        entitlement = CourseEntitlementFactory.create()
        CourseEntitlementFactory.create_batch(2)

        url = reverse(self.ENTITLEMENTS_DETAILS_PATH, args=[str(entitlement.uuid)])

        response = self.client.get(
            url,
            content_type='application/json',
        )
        assert response.status_code == 200

        results = response.data
        assert results == CourseEntitlementSerializer(entitlement).data and results.get('expired_at') is None

    def test_get_expired_entitlement_by_uuid(self):
        past_datetime = now() - timedelta(days=365 * 2)
        entitlement = CourseEntitlementFactory(created=past_datetime)
        CourseEntitlementFactory.create_batch(2)

        CourseEntitlementFactory()
        url = reverse(self.ENTITLEMENTS_DETAILS_PATH, args=[str(entitlement.uuid)])

        response = self.client.get(
            url,
            content_type='application/json',
        )
        assert response.status_code == 200

        results = response.data  # pylint: disable=no-member
        assert results.get('expired_at')

    def test_delete_and_revoke_entitlement(self):
        course_entitlement = CourseEntitlementFactory.create()
        url = reverse(self.ENTITLEMENTS_DETAILS_PATH, args=[str(course_entitlement.uuid)])

        response = self.client.delete(
            url,
            content_type='application/json',
        )
        assert response.status_code == 204
        course_entitlement.refresh_from_db()
        assert course_entitlement.expired_at is not None

    def test_revoke_unenroll_entitlement(self):
        course_entitlement = CourseEntitlementFactory.create()
        url = reverse(self.ENTITLEMENTS_DETAILS_PATH, args=[str(course_entitlement.uuid)])

        enrollment = CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

        course_entitlement.refresh_from_db()
        course_entitlement.enrollment_course_run = enrollment
        course_entitlement.save()

        assert course_entitlement.enrollment_course_run is not None

        response = self.client.delete(
            url,
            content_type='application/json',
        )
        assert response.status_code == 204

        course_entitlement.refresh_from_db()
        assert course_entitlement.expired_at is not None
        assert course_entitlement.enrollment_course_run is None

    def test_reinstate_entitlement(self):
        enrollment = CourseEnrollmentFactory(user=self.user, is_active=True)
        expired_entitlement = CourseEntitlementFactory.create(
            user=self.user, enrollment_course_run=enrollment, expired_at=datetime.now()
        )
        url = reverse(self.ENTITLEMENTS_DETAILS_PATH, args=[str(expired_entitlement.uuid)])

        update_data = {
            'expired_at': None,
            'enrollment_course_run': None,
            'support_details': [
                {
                    'unenrolled_run': str(enrollment.course.id),
                    'action': 'REISSUE',
                    'comments': 'Severe illness.'
                }
            ]
        }

        response = self.client.patch(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200

        results = response.data
        reinstated_entitlement = CourseEntitlement.objects.get(
            uuid=expired_entitlement.uuid
        )
        assert results == CourseEntitlementSerializer(reinstated_entitlement).data


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EntitlementEnrollmentViewSetTest(ModuleStoreTestCase):
    """
    Tests for the EntitlementEnrollmentViewSets
    """
    ENTITLEMENTS_ENROLLMENT_NAMESPACE = 'entitlements_api:v1:enrollments'

    def setUp(self):
        super(EntitlementEnrollmentViewSetTest, self).setUp()
        self.user = UserFactory()
        UserFactory(username=settings.ECOMMERCE_SERVICE_WORKER_USERNAME, is_staff=True)

        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.course = CourseFactory.create(org='edX', number='DemoX', display_name='Demo_Course')
        self.course2 = CourseFactory.create(org='edX', number='DemoX2', display_name='Demo_Course 2')

        self.course_mode = CourseModeFactory(
            course_id=self.course.id,
            mode_slug=CourseMode.VERIFIED,
            # This must be in the future to ensure it is returned by downstream code.
            expiration_datetime=now() + timedelta(days=1)
        )

        self.course_mode = CourseModeFactory(
            course_id=self.course2.id,
            mode_slug=CourseMode.VERIFIED,
            # This must be in the future to ensure it is returned by downstream code.
            expiration_datetime=now() + timedelta(days=1)
        )

        self.return_values = [
            {'key': str(self.course.id)},
            {'key': str(self.course2.id)}
        ]

    @patch("entitlements.api.v1.views.get_course_runs_for_course")
    def test_user_can_enroll(self, mock_get_course_runs):
        course_entitlement = CourseEntitlementFactory.create(user=self.user, mode=CourseMode.VERIFIED)
        mock_get_course_runs.return_value = self.return_values
        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )
        assert course_entitlement.enrollment_course_run is None

        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)
        assert course_entitlement.enrollment_course_run is not None

    @patch("entitlements.api.v1.views.get_course_runs_for_course")
    def test_user_can_unenroll(self, mock_get_course_runs):
        course_entitlement = CourseEntitlementFactory.create(user=self.user, mode=CourseMode.VERIFIED)
        mock_get_course_runs.return_value = self.return_values

        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )
        assert course_entitlement.enrollment_course_run is None

        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)

        response = self.client.delete(
            url,
            content_type='application/json',
        )
        assert response.status_code == 204

        course_entitlement.refresh_from_db()
        assert not CourseEnrollment.is_enrolled(self.user, self.course.id)
        assert course_entitlement.enrollment_course_run is None

    @patch("entitlements.api.v1.views.get_course_runs_for_course")
    def test_user_can_switch(self, mock_get_course_runs):
        mock_get_course_runs.return_value = self.return_values
        course_entitlement = CourseEntitlementFactory.create(user=self.user, mode=CourseMode.VERIFIED)

        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )
        assert course_entitlement.enrollment_course_run is None

        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)

        data = {
            'course_run_id': str(self.course2.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == 201

        course_entitlement.refresh_from_db()
        assert CourseEnrollment.is_enrolled(self.user, self.course2.id)
        assert course_entitlement.enrollment_course_run is not None

    @patch("entitlements.api.v1.views.get_course_runs_for_course")
    def test_user_already_enrolled(self, mock_get_course_runs):
        course_entitlement = CourseEntitlementFactory.create(user=self.user, mode=CourseMode.VERIFIED)
        mock_get_course_runs.return_value = self.return_values

        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )

        CourseEnrollment.enroll(self.user, self.course.id, mode=course_entitlement.mode)
        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)
        assert course_entitlement.enrollment_course_run is not None

    @patch("entitlements.api.v1.views.get_course_runs_for_course")
    def test_user_already_enrolled_in_unpaid_mode(self, mock_get_course_runs):
        course_entitlement = CourseEntitlementFactory.create(user=self.user, mode=CourseMode.VERIFIED)
        mock_get_course_runs.return_value = self.return_values

        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )

        CourseEnrollment.enroll(self.user, self.course.id, mode=CourseMode.AUDIT)
        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)
        (enrolled_mode, is_active) = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        assert is_active and (enrolled_mode == course_entitlement.mode)
        assert course_entitlement.enrollment_course_run is not None

    @patch("entitlements.api.v1.views.get_course_runs_for_course")
    def test_user_cannot_enroll_in_unknown_course_run_id(self, mock_get_course_runs):
        fake_course_str = str(self.course.id) + 'fake'
        fake_course_key = CourseKey.from_string(fake_course_str)
        course_entitlement = CourseEntitlementFactory.create(user=self.user, mode=CourseMode.VERIFIED)
        mock_get_course_runs.return_value = self.return_values

        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )

        data = {
            'course_run_id': str(fake_course_key)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )

        expected_message = 'The Course Run ID is not a match for this Course Entitlement.'
        assert response.status_code == 400
        assert response.data['message'] == expected_message  # pylint: disable=no-member
        assert not CourseEnrollment.is_enrolled(self.user, fake_course_key)

    @patch('entitlements.api.v1.views.refund_entitlement', return_value=True)
    @patch('entitlements.api.v1.views.get_course_runs_for_course')
    def test_user_can_revoke_and_refund(self, mock_get_course_runs, mock_refund_entitlement):
        course_entitlement = CourseEntitlementFactory.create(user=self.user, mode=CourseMode.VERIFIED)
        mock_get_course_runs.return_value = self.return_values

        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )
        assert course_entitlement.enrollment_course_run is None

        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)

        # Unenroll with Revoke for refund
        revoke_url = url + '?is_refund=true'
        response = self.client.delete(
            revoke_url,
            content_type='application/json',
        )
        assert response.status_code == 204

        course_entitlement.refresh_from_db()
        assert mock_refund_entitlement.is_called
        assert (CourseEntitlementSerializer(mock_refund_entitlement.call_args[1]['course_entitlement']).data ==
                CourseEntitlementSerializer(course_entitlement).data)
        assert not CourseEnrollment.is_enrolled(self.user, self.course.id)
        assert course_entitlement.enrollment_course_run is None
        assert course_entitlement.expired_at is not None

    @patch('entitlements.api.v1.views.CourseEntitlement.is_entitlement_refundable', return_value=False)
    @patch('entitlements.api.v1.views.refund_entitlement', return_value=True)
    @patch('entitlements.api.v1.views.get_course_runs_for_course')
    def test_user_can_revoke_and_no_refund_available(
            self,
            mock_get_course_runs,
            mock_refund_entitlement,
            mock_is_refundable
    ):
        course_entitlement = CourseEntitlementFactory.create(user=self.user, mode=CourseMode.VERIFIED)
        mock_get_course_runs.return_value = self.return_values

        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )
        assert course_entitlement.enrollment_course_run is None

        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)

        # Unenroll with Revoke for refund
        revoke_url = url + '?is_refund=true'
        response = self.client.delete(
            revoke_url,
            content_type='application/json',
        )
        assert response.status_code == 400

        course_entitlement.refresh_from_db()
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)
        assert course_entitlement.enrollment_course_run is not None
        assert course_entitlement.expired_at is None

    @patch('entitlements.api.v1.views.CourseEntitlement.is_entitlement_refundable', return_value=True)
    @patch('entitlements.api.v1.views.refund_entitlement', return_value=False)
    @patch("entitlements.api.v1.views.get_course_runs_for_course")
    def test_user_is_not_unenrolled_on_failed_refund(
            self,
            mock_get_course_runs,
            mock_refund_entitlement,
            mock_is_refundable
    ):
        course_entitlement = CourseEntitlementFactory.create(user=self.user, mode=CourseMode.VERIFIED)
        mock_get_course_runs.return_value = self.return_values

        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )
        assert course_entitlement.enrollment_course_run is None

        # Enroll the User
        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)

        # Unenroll with Revoke for refund
        revoke_url = url + '?is_refund=true'
        response = self.client.delete(
            revoke_url,
            content_type='application/json',
        )
        assert response.status_code == 500

        course_entitlement.refresh_from_db()
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)
        assert course_entitlement.enrollment_course_run is not None
        assert course_entitlement.expired_at is None
