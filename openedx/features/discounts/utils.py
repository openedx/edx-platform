"""
Utility functions for working with discounts and discounted pricing.
"""

from django.utils.translation import ugettext as _
from course_modes.models import get_course_prices, format_course_price
from openedx.core.djangolib.markup import HTML

from .applicability import can_receive_discount, discount_percentage


def format_strikeout_price(user, course, base_price=None):
    """
    Return a formatted price, including a struck-out original price if a discount applies, and also
        whether a discount was applied, as the tuple (formatted_price, has_discount).
    """
    if base_price is None:
        base_price = get_course_prices(course, verified_only=True)[0]

    original_price = format_course_price(base_price)

    if can_receive_discount(user, course):
        discount_price = base_price * ((100.0 - discount_percentage()) / 100)
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
                s_sr=HTML("<span class='sr'>"),
                s_op=HTML("<span class='price original'>"),
                e_p=HTML("</span>"),
                e_sr=HTML("</span>"),
            ),
            True
        )
    else:
        return (HTML(u"<span class='price'>{}</span>").format(original_price), False)
