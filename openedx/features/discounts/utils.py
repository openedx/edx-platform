"""
Utility functions for working with discounts and discounted pricing.
"""

from datetime import datetime

import pytz
import six
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from edx_django_utils.cache import RequestCache
from web_fragments.fragment import Fragment

from common.djangoapps.course_modes.models import format_course_price, get_course_prices
from lms.djangoapps.experiments.models import ExperimentData
from lms.djangoapps.courseware.utils import verified_upgrade_deadline_link
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangolib.markup import HTML, Text
from openedx.features.discounts.applicability import (
    REV1008_EXPERIMENT_ID,
    can_receive_discount,
    discount_percentage,
    get_discount_expiration_date
)


def offer_banner_wrapper(user, block, view, frag, context):  # pylint: disable=W0613
    """
    A wrapper that prepends the First Purchase Discount banner if
    the user hasn't upgraded yet.
    """
    if block.category != "vertical":
        return frag

    offer_banner_fragment = get_first_purchase_offer_banner_fragment_from_key(
        user, block.course_id
    )

    if not offer_banner_fragment:
        return frag

    # Course content must be escaped to render correctly due to the way the
    # way the XBlock rendering works. Transforming the safe markup to unicode
    # escapes correctly.
    offer_banner_fragment.content = six.text_type(offer_banner_fragment.content)

    offer_banner_fragment.add_content(frag.content)
    offer_banner_fragment.add_fragment_resources(frag)

    return offer_banner_fragment


def format_strikeout_price(user, course, base_price=None, check_for_discount=True):
    """
    Return a formatted price, including a struck-out original price if a discount applies, and also
        whether a discount was applied, as the tuple (formatted_price, has_discount).
    """
    if base_price is None:
        base_price = get_course_prices(course, verified_only=True)[0]

    original_price = format_course_price(base_price)

    if not check_for_discount or can_receive_discount(user, course):
        discount_price = base_price * ((100.0 - discount_percentage(course)) / 100)
        if discount_price == int(discount_price):
            discount_price = format_course_price("{:0.0f}".format(discount_price))
        else:
            discount_price = format_course_price("{:0.2f}".format(discount_price))

        # Separate out this string because it has a lot of syntax but no actual information for
        # translators to translate
        formatted_discount_price = HTML(
            u"{s_dp}{discount_price}{e_p} {s_st}{s_op}{original_price}{e_p}{e_st}"
        ).format(
            original_price=original_price,
            discount_price=discount_price,
            s_op=HTML("<span class='price original'>"),
            s_dp=HTML("<span class='price discount'>"),
            s_st=HTML("<del aria-hidden='true'>"),
            e_p=HTML("</span>"),
            e_st=HTML("</del>"),
        )

        return (
            HTML(_(
                u"{s_sr}Original price: {s_op}{original_price}{e_p}, discount price: {e_sr}{formatted_discount_price}"
            )).format(
                original_price=original_price,
                formatted_discount_price=formatted_discount_price,
                s_sr=HTML("<span class='sr-only'>"),
                s_op=HTML("<span class='price original'>"),
                e_p=HTML("</span>"),
                e_sr=HTML("</span>"),
            ),
            True
        )
    else:
        return (HTML(u"<span class='price'>{}</span>").format(original_price), False)


def generate_offer_html(user, course):
    """
    Create the actual HTML object with the offer text in it.

    Returns a openedx.core.djangolib.markup.HTML object, or None if the user
    should not be shown an offer message.
    """
    if user and not user.is_anonymous and course:
        now = datetime.now(tz=pytz.UTC).strftime(u"%Y-%m-%d %H:%M:%S%z")
        saw_banner = ExperimentData.objects.filter(
            user=user, experiment_id=REV1008_EXPERIMENT_ID, key=str(course)
        )
        if not saw_banner:
            ExperimentData.objects.create(
                user=user, experiment_id=REV1008_EXPERIMENT_ID, key=str(course), value=now
            )
        discount_expiration_date = get_discount_expiration_date(user, course)
        if (discount_expiration_date and
                can_receive_discount(user=user, course=course, discount_expiration_date=discount_expiration_date)):
            # Translator: xgettext:no-python-format
            offer_message = _(u'{banner_open} Upgrade by {discount_expiration_date} and save {percentage}% '
                              u'[{strikeout_price}]{span_close}{br}Use code {b_open}{code}{b_close} at checkout! '
                              u'{a_open}Upgrade Now{a_close}{div_close}')

            message_html = HTML(offer_message).format(
                a_open=HTML(u'<a id="welcome" href="{upgrade_link}">').format(
                    upgrade_link=verified_upgrade_deadline_link(user=user, course=course)
                ),
                a_close=HTML('</a>'),
                b_open=HTML('<b>'),
                code=Text('BIENVENIDOAEDX') if get_language() == 'es-419' else Text('EDXWELCOME'),
                b_close=HTML('</b>'),
                br=HTML('<br>'),
                banner_open=HTML(
                    '<div class="first-purchase-offer-banner" role="note">'
                    '<span class="first-purchase-offer-banner-bold"><b>'
                ),
                discount_expiration_date=discount_expiration_date.strftime(u'%B %d'),
                percentage=discount_percentage(course),
                span_close=HTML('</b></span>'),
                div_close=HTML('</div>'),
                strikeout_price=HTML(format_strikeout_price(user, course, check_for_discount=False)[0])
            )
            return message_html
    return None


def get_first_purchase_offer_banner_fragment(user, course):
    """
    Return an HTML Fragment with First Purcahse Discount message,
    which has the discount_expiration_date, price,
    discount percentage and a link to upgrade.
    """
    offer_html = generate_offer_html(user, course)
    if offer_html is None:
        return None
    return Fragment(offer_html)


def get_first_purchase_offer_banner_fragment_from_key(user, course_key):
    """
    Like `get_first_purchase_offer_banner_fragment`, but using a CourseKey
    instead of a CourseOverview and using request-level caching.

    Either returns WebFragment to inject XBlock content into, or None if we
    shouldn't show a first purchase offer message for this user.
    """
    request_cache = RequestCache('get_first_purchase_offer_banner_fragment_from_key')
    cache_key = u'html:{},{}'.format(user.id, course_key)
    cache_response = request_cache.get_cached_response(cache_key)
    if cache_response.is_found:
        cached_html = cache_response.value
        if cached_html is None:
            return None
        return Fragment(cached_html)

    course = CourseOverview.get_from_id(course_key)
    offer_html = generate_offer_html(user, course)
    request_cache.set(cache_key, offer_html)

    return Fragment(offer_html)
