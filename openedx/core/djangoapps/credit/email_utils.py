"""
This file contains utility functions which will responsible for sending emails.
"""

import os

import logging
import pynliner
import urlparse
import uuid
import HTMLParser

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.core.mail import EmailMessage, SafeMIMEText
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from eventtracking import tracker

from edxmako.shortcuts import render_to_string
from edxmako.template import Template
from microsite_configuration import microsite
from xmodule.modulestore.django import modulestore


log = logging.getLogger(__name__)


def send_credit_notifications(username, course_key):
    """Sends email notification to user on different phases during credit
    course e.g., credit eligibility, credit payment etc.
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        log.error('No user with %s exist', username)
        return

    course = modulestore().get_course(course_key, depth=0)
    course_display_name = course.display_name
    tracking_context = tracker.get_tracker().resolve_context()
    tracking_id = str(tracking_context.get('user_id'))
    client_id = str(tracking_context.get('client_id'))
    events = '&t=event&ec=email&ea=open'
    tracking_pixel = 'https://www.google-analytics.com/collect?v=1&tid' + tracking_id + '&cid' + client_id + events
    dashboard_link = _email_url_parser('dashboard')
    credit_course_link = _email_url_parser('courses', '?type=credit')

    # get attached branded logo
    logo_image = cache.get('credit.email.attached-logo')
    if logo_image is None:
        branded_logo = {
            'title': 'Logo',
            'path': settings.NOTIFICATION_EMAIL_EDX_LOGO,
            'cid': str(uuid.uuid4())
        }
        logo_image_id = branded_logo['cid']
        logo_image = attach_image(branded_logo, 'Header Logo')
        if logo_image:
            cache.set('credit.email.attached-logo', logo_image, settings.CREDIT_NOTIFICATION_CACHE_TIMEOUT)
    else:
        # strip enclosing angle brackets from 'logo_image' cache 'Content-ID'
        logo_image_id = logo_image.get('Content-ID', '')[1:-1]

    context = {
        'full_name': user.get_full_name(),
        'platform_name': settings.PLATFORM_NAME,
        'course_name': course_display_name,
        'branded_logo': logo_image_id,
        'dashboard_link': dashboard_link,
        'credit_course_link': credit_course_link,
        'tracking_pixel': tracking_pixel,
    }

    # create the root email message
    notification_msg = MIMEMultipart('related')
    # add 'alternative' part to root email message to encapsulate the plain and
    # HTML versions, so message agents can decide which they want to display.
    msg_alternative = MIMEMultipart('alternative')
    notification_msg.attach(msg_alternative)
    # render the credit notification templates
    subject = _(u'Course Credit Eligibility')

    # add alternative plain text message
    email_body_plain = render_to_string('credit_notifications/credit_eligibility_email.txt', context)
    msg_alternative.attach(SafeMIMEText(email_body_plain, _subtype='plain', _charset='utf-8'))

    # add alternative html message
    email_body_content = cache.get('credit.email.css-email-body')
    if email_body_content is None:
        html_file_path = file_path_finder('templates/credit_notifications/credit_eligibility_email.html')
        if html_file_path:
            with open(html_file_path, 'r') as cur_file:
                cur_text = cur_file.read()
                # use html parser to unescape html characters which are changed
                # by the 'pynliner' while adding inline css to html content
                html_parser = HTMLParser.HTMLParser()
                email_body_content = html_parser.unescape(with_inline_css(cur_text))
                # cache the email body content before rendering it since the
                # email context will change for each user e.g., 'full_name'
                cache.set('credit.email.css-email-body', email_body_content, settings.CREDIT_NOTIFICATION_CACHE_TIMEOUT)
        else:
            email_body_content = ''

    email_body = Template(email_body_content).render([context])
    msg_alternative.attach(SafeMIMEText(email_body, _subtype='html', _charset='utf-8'))

    # attach logo image
    if logo_image:
        notification_msg.attach(logo_image)

    # add email addresses of sender and receiver
    from_address = microsite.get_value('default_from_email', settings.DEFAULT_FROM_EMAIL)
    to_address = user.email

    # send the root email message
    msg = EmailMessage(subject, None, from_address, [to_address])
    msg.attach(notification_msg)
    msg.send()


def with_inline_css(html_without_css):
    """Returns html with inline css if the css file path exists
    else returns html with out the inline css.
    """
    css_filepath = settings.NOTIFICATION_EMAIL_CSS
    if not css_filepath.startswith('/'):
        css_filepath = file_path_finder(settings.NOTIFICATION_EMAIL_CSS)

    if css_filepath:
        with open(css_filepath, "r") as _file:
            css_content = _file.read()

        # insert style tag in the html and run pyliner.
        html_with_inline_css = pynliner.fromString('<style>' + css_content + '</style>' + html_without_css)
        return html_with_inline_css

    return html_without_css


def attach_image(img_dict, filename):
    """
    Attach images in the email headers.
    """
    img_path = img_dict['path']
    if not img_path.startswith('/'):
        img_path = file_path_finder(img_path)

    if img_path:
        with open(img_path, 'rb') as img:
            msg_image = MIMEImage(img.read(), name=os.path.basename(img_path))
            msg_image.add_header('Content-ID', '<{}>'.format(img_dict['cid']))
            msg_image.add_header("Content-Disposition", "inline", filename=filename)
        return msg_image


def file_path_finder(path):
    """
    Return physical path of file if found.
    """
    return finders.FileSystemFinder().find(path)


def _email_url_parser(url_name, extra_param=None):
    """Parse url according to 'SITE_NAME' which will be used in the mail.

    Args:
        url_name(str): Name of the url to be parsed
        extra_param(str): Any extra parameters to be added with url if any

    Returns:
        str
    """
    site_name = microsite.get_value('SITE_NAME', settings.SITE_NAME)
    dashboard_url_path = reverse(url_name) + extra_param if extra_param else reverse(url_name)
    dashboard_link_parts = ("https", site_name, dashboard_url_path, '', '', '')
    return urlparse.urlunparse(dashboard_link_parts)
