"""
Tests for ecommerce utils
"""
import httpretty

from django.conf import settings
from mock import patch

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory

from openedx.features.ucsd_features.ecommerce.utils import is_user_eligible_for_discount


class UCSDFeaturesEcommerceUtilsTests(ModuleStoreTestCase):

    def setUpClass(self):
        super(UCSDFeaturesEcommerceUtilsTests, self).setUpClass()
        self.course = CourseFactory.create()

    def setUp(self):
        super(UCSDFeaturesEcommerceUtilsTests, self).setUp()
        self.user = UserFactory()

    def test_is_user_eligible_for_discount_with_disabled_feature(self):
        request = mock.MagicMock()
        course_key = str(self.course.id)
        return_value = is_user_eligible_for_discount(request, course_key)
        self.assertFalse(return_value)
