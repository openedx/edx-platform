""" Helper methods for CourseModes. """


import logging
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from urllib.parse import urljoin  # lint-amnesty, pylint: disable=wrong-import-order

from requests.exceptions import ConnectionError, Timeout  # pylint: disable=redefined-builtin
from slumber.exceptions import SlumberBaseException

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.helpers import VERIFY_STATUS_APPROVED, VERIFY_STATUS_NEED_TO_VERIFY, VERIFY_STATUS_SUBMITTED  # lint-amnesty, pylint: disable=line-too-long
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client

DISPLAY_VERIFIED = "verified"
DISPLAY_HONOR = "honor"
DISPLAY_AUDIT = "audit"
DISPLAY_PROFESSIONAL = "professional"

LOGGER = logging.getLogger(__name__)


def enrollment_mode_display(mode, verification_status, course_id):
    """ Select appropriate display strings and CSS classes.

        Uses mode and verification status to select appropriate display strings and CSS classes
        for certificate display.

        Args:
            mode (str): enrollment mode.
            verification_status (str) : verification status of student

        Returns:
            dictionary:
    """
    show_image = False
    image_alt = ''
    enrollment_title = ''
    enrollment_value = ''
    display_mode = _enrollment_mode_display(mode, verification_status, course_id)

    if display_mode == DISPLAY_VERIFIED:
        if verification_status in [VERIFY_STATUS_NEED_TO_VERIFY, VERIFY_STATUS_SUBMITTED]:
            enrollment_title = _("Your verification is pending")
            enrollment_value = _("Verified: Pending Verification")
            show_image = True
            image_alt = _("ID verification pending")
        elif verification_status == VERIFY_STATUS_APPROVED:
            enrollment_title = _("You're enrolled as a verified student")
            enrollment_value = _("Verified")
            show_image = True
            image_alt = _("ID Verified Ribbon/Badge")
    elif display_mode == DISPLAY_HONOR:
        enrollment_title = _("You're enrolled as an honor code student")
        enrollment_value = _("Honor Code")
    elif display_mode == DISPLAY_PROFESSIONAL:
        enrollment_title = _("You're enrolled as a professional education student")
        enrollment_value = _("Professional Ed")

    return {
        'enrollment_title': str(enrollment_title),
        'enrollment_value': str(enrollment_value),
        'show_image': show_image,
        'image_alt': str(image_alt),
        'display_mode': _enrollment_mode_display(mode, verification_status, course_id)
    }


def _enrollment_mode_display(enrollment_mode, verification_status, course_id):
    """Checking enrollment mode and status and returns the display mode
     Args:
        enrollment_mode (str): enrollment mode.
        verification_status (str) : verification status of student

    Returns:
        display_mode (str) : display mode for certs
    """
    course_mode_slugs = [mode.slug for mode in CourseMode.modes_for_course(course_id)]

    if enrollment_mode == CourseMode.VERIFIED:
        if verification_status in [VERIFY_STATUS_NEED_TO_VERIFY, VERIFY_STATUS_SUBMITTED, VERIFY_STATUS_APPROVED]:
            display_mode = DISPLAY_VERIFIED
        elif DISPLAY_HONOR in course_mode_slugs:
            display_mode = DISPLAY_HONOR
        else:
            display_mode = DISPLAY_AUDIT
    elif enrollment_mode in [CourseMode.PROFESSIONAL, CourseMode.NO_ID_PROFESSIONAL_MODE]:
        display_mode = DISPLAY_PROFESSIONAL
    else:
        display_mode = enrollment_mode

    return display_mode


def get_course_final_price(user, sku, course_price):
    """
    Return the course's discounted price for a user if user is eligible for any otherwise return course original price.
    """
    price_details = {}
    try:
        price_details = ecommerce_api_client(user).baskets.calculate.get(
            sku=[sku],
            username=user.username,
        )
    except (SlumberBaseException, ConnectionError, Timeout) as exc:
        LOGGER.info(
            '[e-commerce calculate endpoint] Exception raise for sku [%s] - user [%s] and exception: %s',
            sku,
            user.username,
            str(exc)
        )

    LOGGER.info(
        '[e-commerce calculate endpoint] The discounted price for sku [%s] and user [%s] is [%s]',
        sku,
        user.username,
        price_details.get('total_incl_tax')
    )
    result = price_details.get('total_incl_tax', course_price)

    # When ecommerce price has zero cents, 'result' gets 149.0
    # As per REV-2260: if zero cents, then only show dollars
    if int(result) == result:
        result = int(result)

    return result


def get_verified_track_links(language):
    """
    Format the URL's for Value Prop's Track Selection verified option, for the specified language.

    Arguments:
        language (str): The language from the user's account settings.

    Returns: dict
        Dictionary with URL's with verified certificate informational links.
        If not edx.org, returns a dictionary with default URL's.
    """
    support_root_url = settings.SUPPORT_SITE_LINK
    marketing_root_url = settings.MKTG_URLS.get('ROOT')

    enabled_languages = {
        'en': 'hc/en-us',
        'es-419': 'hc/es-419',
    }

    # Add edX specific links only to edx.org
    if marketing_root_url and 'edx.org' in marketing_root_url:
        track_verified_url = urljoin(marketing_root_url, 'verified-certificate')
        if support_root_url and 'support.edx.org' in support_root_url:
            support_article_params = '/articles/360013426573-'
            # Must specify the language in the URL since
            # support links do not auto detect the language settings
            language_specific_params = {
                'en': 'What-are-the-differences-between-audit-free-and-verified-paid-courses-',
                'es-419': ('-Cu%C3%A1les-son-las-diferencias'
                           '-entre-los-cursos-de-auditor%C3%ADa-gratuitos-y-verificados-pagos-')
            }
            if language in ('es-419', 'es'):
                full_params = enabled_languages['es-419'] + support_article_params + language_specific_params['es-419']
            else:
                full_params = enabled_languages['en'] + support_article_params + language_specific_params['en']
            track_comparison_url = urljoin(
                support_root_url,
                full_params
            )
            return {
                'verified_certificate': track_verified_url,
                'learn_more': track_comparison_url,
            }
    # Default URL's are used if not edx.org
    return {
        'verified_certificate': marketing_root_url,
        'learn_more': support_root_url,
    }
