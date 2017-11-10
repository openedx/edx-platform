"""
Implements a email notification channel
that sends email to the users.
"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import logging
import datetime
import uuid
import urllib
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import pytz
from edx_notifications import const
from edx_notifications.channels.channel import BaseNotificationChannelProvider
from edx_notifications.digests import attach_image, with_inline_css, get_group_name_for_msg_type
from edx_notifications.renderers.renderer import get_renderer_for_type
from edx_notifications.scopes import resolve_user_scope

from edx_notifications.data import UserNotification

from edx_notifications.channels.link_resolvers import MsgTypeToUrlResolverMixin

log = logging.getLogger(__name__)


class TriggeredEmailChannelProvider(MsgTypeToUrlResolverMixin, BaseNotificationChannelProvider):
    """
    A TriggeredEmail notification channel will
    send email to the user.
    """

    def dispatch_notification_to_user(self, user_id, msg, channel_context=None):
        """
        Send a notification to a user, which - in a TriggerEmailChannel Notification
        """

        # call into one of the registered resolvers to get the email for this
        # user
        scope_results = resolve_user_scope(
            'user_email_resolver',
            {
                'user_id': user_id,
                'fields': {
                    'user_id': True,
                    'email': True,
                    'first_name': True,
                    'last_name': True,
                }
            }
        )
        msg = self._get_linked_resolved_msg(msg)
        msg.created = datetime.datetime.now(pytz.UTC)

        user_msg = UserNotification(
            user_id=user_id,
            msg=msg
        )
        config = const.NOTIFICATION_DIGEST_GROUP_CONFIG
        for result in scope_results:
            #
            # Do the rendering and the sending of the email
            #
            if isinstance(result, dict):
                email = result['email']
            else:
                email = result

            renderer = get_renderer_for_type(user_msg.msg.msg_type)
            notification_html = ''
            if renderer and renderer.can_render_format(const.RENDER_FORMAT_HTML):
                notification_html = renderer.render(  # pylint: disable=unused-variable
                    user_msg.msg,
                    const.RENDER_FORMAT_HTML,
                    None
                )
            # create the image dictionary to store the
            # img_path, unique id and title for the image.
            branded_logo = dict(title='Logo', path=const.NOTIFICATION_BRANDED_DEFAULT_LOGO, cid=str(uuid.uuid4()))

            group_name = get_group_name_for_msg_type(user_msg.msg.msg_type.name)
            resolve_links = user_msg.msg.resolve_links
            click_link = user_msg.msg.payload['_click_link']

            if resolve_links and not click_link.startswith('http'):
                click_link = const.NOTIFICATION_EMAIL_CLICK_LINK_URL_FORMAT.format(
                    url_path=click_link,
                    encoded_url_path=urllib.quote(click_link),
                    user_msg_id=user_msg.id,
                    msg_id=user_msg.msg.id,
                    hostname=const.NOTIFICATION_APP_HOSTNAME
                )

            context = {
                'branded_logo': branded_logo['cid'],
                'notification_html': notification_html,
                'user_first_name': result['first_name'] if isinstance(result, dict) else None,
                'user_last_name': result['last_name'] if isinstance(result, dict) else None,
                'group_name': group_name,
                'group_title': config['groups'][group_name]['display_name'],
                'click_link': click_link
            }

            # render the notifications html template
            email_body = with_inline_css(
                render_to_string("django/triggered_notification_email/triggered_email.html", context))

            html_part = MIMEMultipart(_subtype='related')
            html_part.attach(MIMEText(email_body, _subtype='html'))
            logo_image = attach_image(branded_logo, 'Header Logo')
            if logo_image:
                html_part.attach(logo_image)

            log.info('Sending Notification email to {email}'.format(email=email))

            msg = EmailMessage(const.NOTIFICATION_TRIGGERED_EMAIL_SUBJECT, None,
                               const.NOTIFICATION_EMAIL_FROM_ADDRESS, [email])
            msg.attach(html_part)
            msg.send()
        return user_msg

    def bulk_dispatch_notification(self, user_ids, msg, exclude_user_ids=None, channel_context=None):
        """
        Perform a bulk dispatch of the notification message to
        all user_ids that will be enumerated over in user_ids.

        user_ids should be a list, a generator function, or a
        django.db.models.query.ValuesQuerySet/ValuesListQuerySet
        when directly feeding in a Django ORM queryset, where we select just the id column of the user
        """

        total = 0

        # enumerate through the list of user_ids and call
        # dispatch_notification_to_user method.
        # make sure not to include any user_id in the exclude list
        for user_id in user_ids:
            if not exclude_user_ids or user_id not in exclude_user_ids:
                total += 1
                self.dispatch_notification_to_user(user_id, msg, channel_context)

        return total
