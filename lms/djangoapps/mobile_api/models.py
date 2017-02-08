"""
ConfigurationModel for the mobile_api djangoapp.
"""
from django.db import models

from config_models.models import ConfigurationModel
from .mobile_platform import PLATFORM_CLASSES
from . import utils


class MobileApiConfig(ConfigurationModel):
    """
    Configuration for the video upload feature.

    The order in which the comma-separated list of names of profiles are given
    is in priority order.
    """
    video_profiles = models.TextField(
        blank=True,
        help_text="A comma-separated list of names of profiles to include for videos returned from the mobile API."
    )

    class Meta(object):
        app_label = "mobile_api"

    @classmethod
    def get_video_profiles(cls):
        """
        Get the list of profiles in priority order when requesting from VAL
        """
        return [profile.strip() for profile in cls.current().video_profiles.split(",") if profile]


class AppVersionConfig(models.Model):
    """
    Configuration for mobile app versions available.
    """
    PLATFORM_CHOICES = tuple([
        (platform, platform)
        for platform in PLATFORM_CLASSES.keys()
    ])
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, blank=False)
    version = models.CharField(
        max_length=50,
        blank=False,
        help_text="Version should be in the format X.X.X.Y where X is a number and Y is alphanumeric"
    )
    major_version = models.IntegerField()
    minor_version = models.IntegerField()
    patch_version = models.IntegerField()
    expire_at = models.DateTimeField(null=True, blank=True, verbose_name="Expiry date for platform version")
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "mobile_api"
        unique_together = ('platform', 'version',)
        ordering = ['-major_version', '-minor_version', '-patch_version']

    def __unicode__(self):
        return "{}_{}".format(self.platform, self.version)

    @classmethod
    def latest_version(cls, platform):
        """ Returns latest supported app version for a platform. """
        latest_version_config = cls.objects.filter(platform=platform, enabled=True).first()
        if latest_version_config:
            return latest_version_config.version

    @classmethod
    def last_supported_date(cls, platform, version):
        """ Returns date when app version will get expired for a platform """
        parsed_version = utils.parsed_version(version)
        active_configs = cls.objects.filter(platform=platform, enabled=True, expire_at__isnull=False).reverse()
        for config in active_configs:
            if utils.parsed_version(config.version) >= parsed_version:
                return config.expire_at

    def save(self, *args, **kwargs):
        """ parses version into major, minor and patch versions before saving """
        self.major_version, self.minor_version, self.patch_version = utils.parsed_version(self.version)
        super(AppVersionConfig, self).save(*args, **kwargs)


class IgnoreMobileAvailableFlagConfig(ConfigurationModel):  # pylint: disable=W5101
    """
    Configuration for the mobile_available flag. Default is false.

    Enabling this configuration will cause the mobile_available flag check in
    access.py._is_descriptor_mobile_available to ignore the mobile_available
    flag.
    """

    class Meta(object):
        app_label = "mobile_api"
