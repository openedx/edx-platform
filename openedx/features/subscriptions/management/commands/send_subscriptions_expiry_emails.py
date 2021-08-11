"""
Django management command to send subscription expiry emails to users.
"""
from datetime import date, timedelta
import logging

from django.core.management.base import BaseCommand
from django.db.models import Q
from edx_ace import ace
from edx_ace.recipient import Recipient

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import get_config_value_from_site_or_settings
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.features.edly.context_processor import Colour
from openedx.features.subscriptions.message_types import ExpiredNotification, ImpendingExpiryNotification
from openedx.features.subscriptions.models import UserSubscription
from openedx.features.subscriptions.utils import get_subscription_renew_url

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Send subscripion impending expiry and post expiry email notifications.
    """
    def _get_message_context(self, site):
        """
        """
        message_context = get_base_template_context(site)
        marketing_urls = get_config_value_from_site_or_settings(
            'MKTG_URLS',
            site=site
        )
        marketing_site_root = marketing_urls.get('ROOT', '')
        subscriptions_marketing_url = '{marketing_root_url}subscriptions'.format(
            marketing_root_url='' if not marketing_site_root else marketing_site_root
        )
        message_context['subscriptions_marketing_url'] = subscriptions_marketing_url
        django_settings = get_config_value_from_site_or_settings(
            'DJANGO_SETTINGS_OVERRIDE',
            site=site
        )
        message_context['ecommerce_api_url'] = django_settings['ECOMMERCE_API_URL'] if django_settings else ''
        color_dict = get_config_value_from_site_or_settings(
            'COLORS',
            site=site,
        )

        primary_color = Colour(str(color_dict.get('primary')))

        message_context.update({
            'edly_fonts_config': get_config_value_from_site_or_settings(
                'FONTS',
                site=site,
            ),
            'edly_branding_config': get_config_value_from_site_or_settings(
                'BRANDING',
                site=site,
            ),
            'edly_copyright_text': get_config_value_from_site_or_settings(
                'EDLY_COPYRIGHT_TEXT',
                site=site,
            ),
            'edly_colors_config': {'primary': primary_color},
        })

        return message_context

    def _send_email_notifications(self, context_values, ace_message_class):
        """
        Send email notifications from the given context values.
        """
        for subscription_id, user, site in context_values:
            message_context = self._get_message_context(site)
            if ace_message_class == ExpiredNotification:
                subscription_renew_url = get_subscription_renew_url(
                    subscription_id,
                    user,
                    message_context['ecommerce_api_url']
                )
                message_context.update({
                    'subscription_renew_url': subscription_renew_url,
                    'subscription_id': subscription_id,
                })

            try:
                with emulate_http_request(site=site, user=user):
                    msg = ace_message_class(context=message_context).personalize(
                        recipient=Recipient(user.username, user.email),
                        language=get_user_preference(user, LANGUAGE_KEY),
                        user_context={'full_name': user.profile.name}
                    )
                    ace.send(msg)
                    logger.info('Expiry notification email sent to user: %r', user.username)

            except Exception:  # pylint: disable=broad-except
                logger.exception('Could not send email for subscription expiry notification to user %s', user.username)

    def handle(self, *args, **options):
        """
        Send expiry emails to relevant users.
        """
        impending_expiry_subscriptions = UserSubscription.objects.filter(
            Q(expiration_date__isnull=False) & Q(expiration_date=date.today() + timedelta(days=1))
        )
        impending_expiry_subscriptions_context_values = [
            (subscription.subscription_id, subscription.user, subscription.site)
            for subscription in impending_expiry_subscriptions
        ]

        expired_subscriptions = UserSubscription.objects.filter(
            Q(expiration_date__isnull=False) & Q(expiration_date=date.today() - timedelta(days=1))
        )
        expired_subscriptions_context_values = [
            (subscription.subscription_id, subscription.user, subscription.site)
            for subscription in expired_subscriptions
        ]

        self._send_email_notifications(
            impending_expiry_subscriptions_context_values,
            ImpendingExpiryNotification
        )

        self._send_email_notifications(
            expired_subscriptions_context_values,
            ExpiredNotification
        )
