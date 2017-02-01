"""
Tests for Platform against Mobile App Request
"""
import ddt
from django.test import TestCase
from mobile_api.mobile_platform import MobilePlatform


@ddt.ddt
class TestMobilePlatform(TestCase):
    """
    Tests for platform against mobile app request
    """
    def setUp(self):
        super(TestMobilePlatform, self).setUp()

    @ddt.data(
        ("edX/org.edx.mobile (0.1.5; OS Version 9.2 (Build 13C75))", "iOS", "0.1.5"),
        ("edX/org.edx.mobile (1.01.1; OS Version 9.2 (Build 13C75))", "iOS", "1.01.1"),
        ("edX/org.edx.mobile (2.2.2; OS Version 9.2 (Build 13C75))", "iOS", "2.2.2"),
        ("edX/org.edx.mobile (3.3.3; OS Version 9.2 (Build 13C75))", "iOS", "3.3.3"),
        ("edX/org.edx.mobile (3.3.3.test; OS Version 9.2 (Build 13C75))", "iOS", "3.3.3.test"),
        ("edX/org.test-domain.mobile (0.1.5; OS Version 9.2 (Build 13C75))", "iOS", "0.1.5"),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/1.1.1", "Android", "1.1.1"),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/2.2.2", "Android", "2.2.2"),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/3.3.3", "Android", "3.3.3"),
        ("Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/3.3.3.X", "Android", "3.3.3.X"),
    )
    @ddt.unpack
    def test_platform_instance(self, user_agent, platform_name, version):
        platform = MobilePlatform.get_instance(user_agent)
        self.assertEqual(platform_name, platform.NAME)
        self.assertEqual(version, platform.version)

    @ddt.data(
        ("Mozilla/5.0 (Linux; Android 5.1; Nexus 5 Build/LMY47I; wv) AppleWebKit/537.36 (KHTML, like Gecko) "
         "Version/4.0 Chrome/47.0.2526.100 Mobile Safari/537.36 edX/org.edx.mobile/2.0.0"),
        ("Mozilla/5.0 (iPhone; CPU iPhone OS 9_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) "
         "Mobile/13C75 edX/org.edx.mobile/2.2.1"),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 "
         "Safari/537.36"),
        "edX/org.edx.mobile (0.1.5.2.; OS Version 9.2 (Build 13C75))",
        "edX/org.edx.mobile (0.1.5.2.5.1; OS Version 9.2 (Build 13C75))",
    )
    def test_non_mobile_app_requests(self, user_agent):
        self.assertIsNone(MobilePlatform.get_instance(user_agent))
