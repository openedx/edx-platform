"""
Email-marketing-related models.
"""


from config_models.models import ConfigurationModel
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class EmailMarketingConfiguration(ConfigurationModel):
    """
    Email marketing configuration

    .. no_pii:
    """

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

    sailthru_welcome_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru template to use on welcome send."
        )
    )

    sailthru_abandoned_cart_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru template to use on abandoned cart reminder. Deprecated."
        )
    )

    sailthru_abandoned_cart_delay = models.fields.IntegerField(
        default=60,
        help_text=_(
            "Sailthru minutes to wait before sending abandoned cart message. Deprecated."
        )
    )

    sailthru_enroll_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru send template to use on enrolling for audit. "
        )
    )

    sailthru_verification_passed_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru send template to use on passed ID verification."
        )
    )

    sailthru_verification_failed_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru send template to use on failed ID verification."
        )
    )

    sailthru_upgrade_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru send template to use on upgrading a course. Deprecated "
        )
    )

    sailthru_purchase_template = models.fields.CharField(
        max_length=20,
        blank=True,
        help_text=_(
            "Sailthru send template to use on purchasing a course seat. Deprecated "
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

    sailthru_lms_url_override = models.fields.CharField(
        max_length=80,
        blank=True,
        help_text=_(
            "Optional lms url scheme + host used to construct urls for content library, e.g. https://courses.edx.org."
        )
    )

    # The number of seconds to delay for welcome emails sending. This is needed to acommendate those
    # learners who created user account during course enrollment so we can send a different message
    # in our welcome email.
    welcome_email_send_delay = models.fields.IntegerField(
        default=600,
        help_text=_(
            "Number of seconds to delay the sending of User Welcome email after user has been created"
        )
    )

    # The number of seconds to delay/timeout wait to get cookie values from sailthru.
    user_registration_cookie_timeout_delay = models.fields.FloatField(
        default=3.0,
        help_text=_(
            "The number of seconds to delay/timeout wait to get cookie values from sailthru."
        )
    )

    def __str__(self):
        return u"Email marketing configuration: New user list %s, Welcome template: %s" % \
               (self.sailthru_new_user_list, self.sailthru_welcome_template)
