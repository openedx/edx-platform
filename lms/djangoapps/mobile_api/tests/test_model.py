"""
Tests for Mobile API Configuration Models
"""
from datetime import datetime
import ddt
from django.test import TestCase
from pytz import UTC
from mobile_api.models import AppVersionConfig, MobileApiConfig


@ddt.ddt
class TestAppVersionConfigModel(TestCase):
    """
    Tests for app version configuration model
    """
    def setUp(self):
        super(TestAppVersionConfigModel, self).setUp()

    def set_app_version_config(self):
        """ Creates configuration data for platform versions """
        AppVersionConfig(platform="ios", version="1.1.1", expire_at=None, enabled=True).save()
        AppVersionConfig(
            platform="ios",
            version="2.2.2",
            expire_at=datetime(2014, 01, 01, tzinfo=UTC),
            enabled=True
        ).save()
        AppVersionConfig(
            platform="ios",
            version="4.1.1",
            expire_at=datetime(5000, 01, 01, tzinfo=UTC),
            enabled=False
        ).save()
        AppVersionConfig(
            platform="ios",
            version="4.4.4",
            expire_at=datetime(9000, 01, 01, tzinfo=UTC),
            enabled=True
        ).save()
        AppVersionConfig(platform="ios", version="6.6.6", expire_at=None, enabled=True).save()
        AppVersionConfig(platform="ios", version="8.8.8", expire_at=None, enabled=False).save()

        AppVersionConfig(platform="android", version="1.1.1", expire_at=None, enabled=True).save()
        AppVersionConfig(
            platform="android",
            version="2.2.2",
            expire_at=datetime(2014, 01, 01, tzinfo=UTC),
            enabled=True
        ).save()
        AppVersionConfig(
            platform="android",
            version="4.4.4",
            expire_at=datetime(9000, 01, 01, tzinfo=UTC),
            enabled=True
        ).save()
        AppVersionConfig(platform="android", version="8.8.8", expire_at=None, enabled=True).save()

    @ddt.data(
        ('ios', '4.4.4'),
        ('ios', '6.6.6'),
        ("android", '4.4.4'),
        ('android', '8.8.8')
    )
    @ddt.unpack
    def test_no_configs_available(self, platform, version):
        self.assertIsNone(AppVersionConfig.latest_version(platform))
        self.assertIsNone(AppVersionConfig.last_supported_date(platform, version))

    @ddt.data(('ios', '6.6.6'), ('android', '8.8.8'))
    @ddt.unpack
    def test_latest_version(self, platform, latest_version):
        self.set_app_version_config()
        self.assertEqual(latest_version, AppVersionConfig.latest_version(platform))

    @ddt.data(
        ('ios', '3.3.3', datetime(9000, 1, 1, tzinfo=UTC)),
        ('ios', '4.4.4', datetime(9000, 1, 1, tzinfo=UTC)),
        ('ios', '6.6.6', None),
        ("android", '4.4.4', datetime(9000, 1, 1, tzinfo=UTC)),
        ('android', '8.8.8', None)
    )
    @ddt.unpack
    def test_last_supported_date(self, platform, version, last_supported_date):
        self.set_app_version_config()
        self.assertEqual(last_supported_date, AppVersionConfig.last_supported_date(platform, version))


class TestMobileApiConfig(TestCase):
    """
    Tests MobileAPIConfig
    """

    def test_video_profile_list(self):
        """Check that video_profiles config is returned in order as a list"""
        MobileApiConfig(video_profiles="mobile_low,mobile_high,youtube").save()
        video_profile_list = MobileApiConfig.get_video_profiles()
        self.assertEqual(
            video_profile_list,
            [u'mobile_low', u'mobile_high', u'youtube']
        )

    def test_video_profile_list_with_whitespace(self):
        """Check video_profiles config with leading and trailing whitespace"""
        MobileApiConfig(video_profiles=" mobile_low , mobile_high,youtube ").save()
        video_profile_list = MobileApiConfig.get_video_profiles()
        self.assertEqual(
            video_profile_list,
            [u'mobile_low', u'mobile_high', u'youtube']
        )

    def test_empty_video_profile(self):
        """Test an empty video_profile"""
        MobileApiConfig(video_profiles="").save()
        video_profile_list = MobileApiConfig.get_video_profiles()
        self.assertEqual(video_profile_list, [])
