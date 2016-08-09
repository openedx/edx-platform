"""
Tests for Version Based App Upgrade Middleware
"""
from datetime import datetime
import ddt
from django.core.cache import caches
from django.http import HttpRequest, HttpResponse
import mock
from pytz import UTC
from mobile_api.middleware import AppVersionUpgrade
from mobile_api.models import AppVersionConfig
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase


@ddt.ddt
class TestAppVersionUpgradeMiddleware(CacheIsolationTestCase):
    """
    Tests for version based app upgrade middleware
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestAppVersionUpgradeMiddleware, self).setUp()
        self.middleware = AppVersionUpgrade()
        self.set_app_version_config()

    def set_app_version_config(self):
        """ Creates configuration data for platform versions """
        AppVersionConfig(platform="iOS", version="1.1.1", expire_at=None, enabled=True).save()
        AppVersionConfig(
            platform="iOS",
            version="2.2.2",
            expire_at=datetime(2014, 01, 01, tzinfo=UTC),
            enabled=True
        ).save()
        AppVersionConfig(
            platform="iOS",
            version="4.4.4",
            expire_at=datetime(9000, 01, 01, tzinfo=UTC),
            enabled=True
        ).save()
        AppVersionConfig(platform="iOS", version="6.6.6", expire_at=None, enabled=True).save()

        AppVersionConfig(platform="Android", version="1.1.1", expire_at=None, enabled=True).save()
        AppVersionConfig(
            platform="Android",
            version="2.2.2",
            expire_at=datetime(2014, 01, 01, tzinfo=UTC),
            enabled=True
        ).save()
        AppVersionConfig(
            platform="Android",
            version="4.4.4",
            expire_at=datetime(5000, 01, 01, tzinfo=UTC),
            enabled=True
        ).save()
        AppVersionConfig(platform="Android", version="8.8.8", expire_at=None, enabled=True).save()

    def process_middleware(self, user_agent, cache_get_many_calls_for_request=1):
        """ Helper function that makes calls to middle process_request and process_response """
        fake_request = HttpRequest()
        fake_request.META['HTTP_USER_AGENT'] = user_agent
        with mock.patch.object(caches['default'], 'get_many', wraps=caches['default'].get_many) as mocked_code:
            request_response = self.middleware.process_request(fake_request)
            self.assertEqual(cache_get_many_calls_for_request, mocked_code.call_count)
        with mock.patch.object(caches['default'], 'get_many', wraps=caches['default'].get_many) as mocked_code:
            processed_response = self.middleware.process_response(fake_request, request_response or HttpResponse())
            self.assertEqual(0, mocked_code.call_count)
        return request_response, processed_response

    @ddt.data(
        ("Mozilla/5.0 (Linux; Android 5.1; Nexus 5 Build/LMY47I; wv) AppleWebKit/537.36 (KHTML, like Gecko) "
         "Version/4.0 Chrome/47.0.2526.100 Mobile Safari/537.36 edX/org.edx.mobile/2.0.0"),
        ("Mozilla/5.0 (iPhone; CPU iPhone OS 9_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) "
         "Mobile/13C75 edX/org.edx.mobile/2.2.1"),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 "
         "Safari/537.36"),
    )
    def test_non_mobile_app_requests(self, user_agent):
        with self.assertNumQueries(0):
            request_response, processed_response = self.process_middleware(user_agent, 0)
        self.assertIsNone(request_response)
        self.assertEquals(200, processed_response.status_code)
        self.assertNotIn(AppVersionUpgrade.LATEST_VERSION_HEADER, processed_response)
        self.assertNotIn(AppVersionUpgrade.LAST_SUPPORTED_DATE_HEADER, processed_response)

    @ddt.data(
        "edX/org.edx.mobile (6.6.6; OS Version 9.2 (Build 13C75))",
        "edX/org.edx.mobile (7.7.7; OS Version 9.2 (Build 13C75))",
        "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/8.8.8",
        "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/9.9.9",
    )
    def test_no_update(self, user_agent):
        with self.assertNumQueries(2):
            request_response, processed_response = self.process_middleware(user_agent)
        self.assertIsNone(request_response)
        self.assertEquals(200, processed_response.status_code)
        self.assertNotIn(AppVersionUpgrade.LATEST_VERSION_HEADER, processed_response)
        self.assertNotIn(AppVersionUpgrade.LAST_SUPPORTED_DATE_HEADER, processed_response)
        with self.assertNumQueries(0):
            self.process_middleware(user_agent)

    @ddt.data(
        ("edX/org.edx.mobile (5.1.1; OS Version 9.2 (Build 13C75))", "6.6.6"),
        ("edX/org.edx.mobile (5.1.1.RC; OS Version 9.2 (Build 13C75))", "6.6.6"),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/5.1.1", "8.8.8"),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/5.1.1.RC", "8.8.8"),
    )
    @ddt.unpack
    def test_new_version_available(self, user_agent, latest_version):
        with self.assertNumQueries(2):
            request_response, processed_response = self.process_middleware(user_agent)
        self.assertIsNone(request_response)
        self.assertEquals(200, processed_response.status_code)
        self.assertEqual(latest_version, processed_response[AppVersionUpgrade.LATEST_VERSION_HEADER])
        self.assertNotIn(AppVersionUpgrade.LAST_SUPPORTED_DATE_HEADER, processed_response)
        with self.assertNumQueries(0):
            self.process_middleware(user_agent)

    @ddt.data(
        ("edX/org.edx.mobile (1.0.1; OS Version 9.2 (Build 13C75))", "6.6.6"),
        ("edX/org.edx.mobile (1.1.1; OS Version 9.2 (Build 13C75))", "6.6.6"),
        ("edX/org.edx.mobile (2.0.5.RC; OS Version 9.2 (Build 13C75))", "6.6.6"),
        ("edX/org.edx.mobile (2.2.2; OS Version 9.2 (Build 13C75))", "6.6.6"),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/1.0.1", "8.8.8"),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/1.1.1", "8.8.8"),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/2.0.5.RC", "8.8.8"),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/2.2.2", "8.8.8"),
    )
    @ddt.unpack
    def test_version_update_required(self, user_agent, latest_version):
        with self.assertNumQueries(2):
            request_response, processed_response = self.process_middleware(user_agent)
        self.assertIsNotNone(request_response)
        self.assertEquals(426, processed_response.status_code)
        self.assertEqual(latest_version, processed_response[AppVersionUpgrade.LATEST_VERSION_HEADER])
        with self.assertNumQueries(0):
            self.process_middleware(user_agent)

    @ddt.data(
        ("edX/org.edx.mobile (4.4.4; OS Version 9.2 (Build 13C75))", "6.6.6", '9000-01-01T00:00:00+00:00'),
        (
            "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/4.4.4",
            "8.8.8",
            '5000-01-01T00:00:00+00:00',
        ),
    )
    @ddt.unpack
    def test_version_update_available_with_deadline(self, user_agent, latest_version, upgrade_date):
        with self.assertNumQueries(2):
            request_response, processed_response = self.process_middleware(user_agent)
        self.assertIsNone(request_response)
        self.assertEquals(200, processed_response.status_code)
        self.assertEqual(latest_version, processed_response[AppVersionUpgrade.LATEST_VERSION_HEADER])
        self.assertEqual(upgrade_date, processed_response[AppVersionUpgrade.LAST_SUPPORTED_DATE_HEADER])
        with self.assertNumQueries(0):
            self.process_middleware(user_agent)
