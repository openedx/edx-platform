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
        blank=True,
        help_text=_(
            "Sailthru template to use on activation send. "
        )
    )

    sailthru_abandoned_cart_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru template to use on abandoned cart reminder. "
        )
    )

    sailthru_abandoned_cart_delay = models.fields.IntegerField(
        default=60,
        help_text=_(
            "Sailthru minutes to wait before sending abandoned cart message."
        )
    )

    sailthru_enroll_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru send template to use on enrolling for audit. "
        )
    )

    sailthru_upgrade_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru send template to use on upgrading a course. "
        )
    )

    sailthru_purchase_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru send template to use on purchasing a course seat. "
        )
    )

    # Sailthru purchases can be tagged with interest tags to provide information about the types of courses
    # users are interested in.  The easiest way to get the tags currently is the Sailthru content API which
    # looks in the content library (the content library is populated daily with a script that pulls the data
    # from the course discovery API)  This option should normally be on, but it does add overhead to processing
    # purchases and enrolls.
    sailthru_get_tags_from_sailthru = models.BooleanField(
        default=True,
        help_text=_('Use the Sailthru content API to fetch course tags.')
    )

    sailthru_content_cache_age = models.fields.IntegerField(
        default=3600,
        help_text=_(
            "Number of seconds to cache course content retrieved from Sailthru."
        )
    )

    sailthru_enroll_cost = models.fields.IntegerField(
        default=100,
        help_text=_(
            "Cost in cents to report to Sailthru for enrolls."
        )
    )

    def __unicode__(self):
        return u"Email marketing configuration: New user list %s, Activation template: %s" % \
               (self.sailthru_new_user_list, self.sailthru_activation_template)
