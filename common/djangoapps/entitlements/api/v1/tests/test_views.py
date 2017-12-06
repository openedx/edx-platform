import json
import unittest
import uuid
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.core.urlresolvers import reverse

from student.tests.factories import (TEST_PASSWORD, CourseEnrollmentFactory, UserFactory)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

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
        self.entitlements_list_url = reverse('entitlements_api:v1:entitlements-list')

    def _get_data_set(self, user, course_uuid):
        """
        Get a basic data set for an entitlement
        """
        return {
            "user": user.username,
            "mode": "verified",
            "course_uuid": course_uuid,
            "order_number": "EDX-1001"
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

        course_entitlement = CourseEntitlementFactory()
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

    def test_staff_not_get_all_entitlements(self):
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
        past_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(days=365 * 2)
        entitlements = CourseEntitlementFactory.create_batch(2, created=past_datetime, user=self.user)

        # Set the first entitlement to be at a time that it isn't expired
        entitlements[0].created = datetime.utcnow()
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
        past_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(days=365 * 2)
        not_staff_user = UserFactory()
        self.client.login(username=not_staff_user.username, password=TEST_PASSWORD)
        entitlement_user2 = CourseEntitlementFactory.create_batch(2, user=not_staff_user, created=past_datetime)
        url = reverse('entitlements_api:v1:entitlements-list')
        url += '?user={username}'.format(username=not_staff_user.username)

        # Set the first entitlement to be at a time that it isn't expired
        entitlement_user2[0].created = datetime.utcnow()
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
        entitlement = CourseEntitlementFactory()
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
        past_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(days=365 * 2)
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
