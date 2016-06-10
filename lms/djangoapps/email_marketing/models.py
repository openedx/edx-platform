"""
Email-marketing-related models.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _

from config_models.models import ConfigurationModel


class EmailMarketingConfiguration(ConfigurationModel):
    """ Email marketing configuration """

    class Meta(object):
        app_label = "email_marketing"

    sailthru_key = models.fields.CharField(
        max_length=32,
        help_text=_(
            "API key for accessing Sailthru. "
        )
    )

    sailthru_secret = models.fields.CharField(
        max_length=32,
        help_text=_(
            "API secret for accessing Sailthru. "
        )
    )

    sailthru_new_user_list = models.fields.CharField(
        max_length=48,
        help_text=_(
            "Sailthru list name to add new users to. "
        )
    )

    sailthru_retry_interval = models.fields.IntegerField(
        default=3600,
        help_text=_(
            "Sailthru connection retry interval (secs)."
        )
    )

    sailthru_max_retries = models.fields.IntegerField(
        default=24,
        help_text=_(
            "Sailthru maximum retries."
        )
    )

    sailthru_activation_template = models.fields.CharField(
        max_length=20,
        help_text=_(
            "Sailthru template to use on activation send. "
        )
    )

    def __unicode__(self):
        return u"Email marketing configuration: New user list %s, Activation template: %s" % \
               (self.sailthru_new_user_list, self.sailthru_activation_template)
