"""
Tests for ecommerce utils
"""
import httpretty
import mock

from django.conf import settings
from django.test.utils import override_settings
from mock import patch

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory

from openedx.features.ucsd_features.ecommerce.utils import is_user_eligible_for_discount
from openedx.features.ucsd_features.ecommerce.tests.utils import make_ecommerce_url


class UCSDFeaturesEcommerceUtilsTests(ModuleStoreTestCase):

    def setUp(self):
        super(UCSDFeaturesEcommerceUtilsTests, self).setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create()

    def test_is_user_eligible_for_discount_with_disabled_feature(self):
        features = settings.FEATURES.copy()
        features['ENABLE_GEOGRAPHIC_DISCOUNTS'] = False
        with override_settings(FEATURES=features):
            request = mock.MagicMock()
            course_key = str(self.course.id)
            return_value = is_user_eligible_for_discount(request, course_key)
            self.assertFalse(return_value)

    def test_is_user_eligible_for_discount_when_country_code_is_not_eligible(self):
        features = settings.FEATURES.copy()
        features['ENABLE_GEOGRAPHIC_DISCOUNTS'] = True
        with override_settings(FEATURES=features):
            eligible_countries = settings.COUNTRIES_ELIGIBLE_FOR_DISCOUNTS
            eligible_countries = {
                'PK': 'Pakistan'
            }
            with override_settings(COUNTRIES_ELIGIBLE_FOR_DISCOUNTS=eligible_countries):
                request = mock.MagicMock()
                request.session = {
                    'country_code': 'US'
                }
                request.user = self.user

                course_key = str(self.course.id)
                return_value = is_user_eligible_for_discount(request, course_key)
                self.assertFalse(return_value)

    @httpretty.activate
    def test_is_user_eligible_for_discount_when_course_is_not_eligible(self):
        url = make_ecommerce_url('/ucsd/api/v1/check_course_coupon/')
        course_key = str(self.course.id)

        httpretty.register_uri(
            httpretty.POST,
            url,
            status=400,
            body='{}',
            content_type='application/json'
        )

        features = settings.FEATURES.copy()
        features['ENABLE_GEOGRAPHIC_DISCOUNTS'] = True

        with override_settings(FEATURES=features):
            eligible_countries = settings.COUNTRIES_ELIGIBLE_FOR_DISCOUNTS
            eligible_countries = {
                'US': 'United States of America'
            }
            with override_settings(COUNTRIES_ELIGIBLE_FOR_DISCOUNTS=eligible_countries):
                request = mock.MagicMock()
                request.session = {
                    'country_code': 'US'
                }
                request.user = self.user

                return_value = is_user_eligible_for_discount(request, course_key)
                self.assertFalse(return_value)

    @httpretty.activate
    def test_is_user_eligible_for_discount_when_course_is_not_eligible(self):
        url = make_ecommerce_url('/ucsd/api/v1/check_course_coupon/')
        course_key = str(self.course.id)

        httpretty.register_uri(
            httpretty.POST,
            url,
            status=200,
            body='{}',
            content_type='application/json'
        )

        features = settings.FEATURES.copy()
        features['ENABLE_GEOGRAPHIC_DISCOUNTS'] = True

        with override_settings(FEATURES=features):
            eligible_countries = settings.COUNTRIES_ELIGIBLE_FOR_DISCOUNTS
            eligible_countries = {
                'US': 'United States of America'
            }
            with override_settings(COUNTRIES_ELIGIBLE_FOR_DISCOUNTS=eligible_countries):
                request = mock.MagicMock()
                request.session = {
                    'country_code': 'US'
                }
                request.user = self.user

                return_value = is_user_eligible_for_discount(request, course_key)
                self.assertTrue(return_value)
