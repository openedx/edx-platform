"""
Signal handling functions for use with external commerce service.
"""
from __future__ import unicode_literals

import json
import logging
from urlparse import urljoin

import requests
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from edx_rest_api_client.exceptions import HttpClientError
from request_cache.middleware import RequestCache
from student.models import UNENROLL_DONE

from openedx.core.djangoapps.commerce.utils import ecommerce_api_client, is_commerce_service_configured
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming import helpers as theming_helpers
from util.views import create_helpdesk_ticket

log = logging.getLogger(__name__)


@receiver(UNENROLL_DONE)
def handle_unenroll_done(sender, course_enrollment=None, skip_refund=False,
                         **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver for unenrollments, used to automatically initiate refunds
    when applicable.

    N.B. this signal is also consumed by lms.djangoapps.shoppingcart.
    """
    if not is_commerce_service_configured() or skip_refund:
        return

    if course_enrollment and course_enrollment.refundable():
        try:
            request_user = get_request_user() or course_enrollment.user
            if isinstance(request_user, AnonymousUser):
                # Assume the request was initiated via server-to-server
                # api call (presumably Otto).  In this case we cannot
                # construct a client to call Otto back anyway, because
                # the client does not work anonymously, and furthermore,
                # there's certainly no need to inform Otto about this request.
                return
            refund_seat(course_enrollment, request_user)
        except:  # pylint: disable=bare-except
            # don't assume the signal was fired with `send_robust`.
            # avoid blowing up other signal handlers by gracefully
            # trapping the Exception and logging an error.
            log.exception(
                "Unexpected exception while attempting to initiate refund for user [%s], course [%s]",
                course_enrollment.user.id,
                course_enrollment.course_id,
            )


def get_request_user():
    """
    Helper to get the authenticated user from the current HTTP request (if
    applicable).

    If the requester of an unenrollment is not the same person as the student
    being unenrolled, we authenticate to the commerce service as the requester.
    """
    request = RequestCache.get_current_request()
    return getattr(request, 'user', None)


def refund_seat(course_enrollment, request_user):
    """
    Attempt to initiate a refund for any orders associated with the seat being
    unenrolled, using the commerce service.

    Arguments:
        course_enrollment (CourseEnrollment): a student enrollment
        request_user: the user as whom to authenticate to the commerce service
            when attempting to initiate the refund.

    Returns:
        A list of the external service's IDs for any refunds that were initiated
            (may be empty).

    Raises:
        exceptions.SlumberBaseException: for any unhandled HTTP error during
            communication with the commerce service.
        exceptions.Timeout: if the attempt to reach the commerce service timed
            out.

    """
    course_key_str = unicode(course_enrollment.course_id)
    unenrolled_user = course_enrollment.user

    try:
        refund_ids = ecommerce_api_client(request_user or unenrolled_user).refunds.post(
            {'course_id': course_key_str, 'username': unenrolled_user.username}
        )
    except HttpClientError, exc:
        if exc.response.status_code == 403 and request_user != unenrolled_user:
            # this is a known limitation; commerce service does not presently
            # support the case of a non-superusers initiating a refund on
            # behalf of another user.
            log.warning("User [%s] was not authorized to initiate a refund for user [%s] "
                        "upon unenrollment from course [%s]", request_user.id, unenrolled_user.id, course_key_str)
            return []
        else:
            # no other error is anticipated, so re-raise the Exception
            raise exc

    if refund_ids:
        # at least one refundable order was found.
        log.info(
            "Refund successfully opened for user [%s], course [%s]: %r",
            unenrolled_user.id,
            course_key_str,
            refund_ids,
        )

        # XCOM-371: this is a temporary measure to suppress refund-related email
        # notifications to students and support@) for free enrollments.  This
        # condition should be removed when the CourseEnrollment.refundable() logic
        # is updated to be more correct, or when we implement better handling (and
        # notifications) in Otto for handling reversal of $0 transactions.
        if course_enrollment.mode != 'verified':
            # 'verified' is the only enrollment mode that should presently
            # result in opening a refund request.
            log.info(
                "Skipping refund email notification for non-verified mode for user [%s], course [%s], mode: [%s]",
                course_enrollment.user.id,
                course_enrollment.course_id,
                course_enrollment.mode,
            )
        else:
            try:
                send_refund_notification(course_enrollment, refund_ids)
            except:  # pylint: disable=bare-except
                # don't break, just log a warning
                log.warning("Could not send email notification for refund.", exc_info=True)
    else:
        # no refundable orders were found.
        log.debug("No refund opened for user [%s], course [%s]", unenrolled_user.id, course_key_str)

    return refund_ids


def generate_refund_notification_body(student, refund_ids):  # pylint: disable=invalid-name
    """ Returns a refund notification message body. """
    msg = _(
        "A refund request has been initiated for {username} ({email}). "
        "To process this request, please visit the link(s) below."
    ).format(username=student.username, email=student.email)

    ecommerce_url_root = configuration_helpers.get_value(
        'ECOMMERCE_PUBLIC_URL_ROOT', settings.ECOMMERCE_PUBLIC_URL_ROOT,
    )
    refund_urls = [urljoin(ecommerce_url_root, '/dashboard/refunds/{}/'.format(refund_id))
                   for refund_id in refund_ids]

    return '{msg}\n\n{urls}'.format(msg=msg, urls='\n'.join(refund_urls))


def send_refund_notification(course_enrollment, refund_ids):
    """ Notify the support team of the refund request. """

    tags = ['auto_refund']

    if theming_helpers.is_request_in_themed_site():
        # this is not presently supported with the external service.
        raise NotImplementedError("Unable to send refund processing emails to support teams.")

    student = course_enrollment.user
    subject = _("[Refund] User-Requested Refund")
    body = generate_refund_notification_body(student, refund_ids)
    requester_name = student.profile.name or student.username

    create_helpdesk_ticket(requester_name, student.email, subject, body, tags)
