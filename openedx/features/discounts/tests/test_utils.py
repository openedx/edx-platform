"""
Tests of the openedx.features.discounts.utils module.
"""
from unittest import TestCase
from mock import patch, Mock
import six

import ddt

from .. import utils


@ddt.ddt
class TestStrikeoutPrice(TestCase):
    """
    Tests of the strike-out pricing for discounts.
    """
    def test_not_eligible(self):
        with patch.multiple(
            utils,
            can_receive_discount=Mock(return_value=False),
            get_course_prices=Mock(return_value=(100, None))
        ):
            content, has_discount = utils.format_strikeout_price(Mock(name='user'), Mock(name='course'))

        assert six.text_type(content) == u"<span class='price'>$100</span>"
        assert not has_discount

    @ddt.data((15, 100, "$100", "$85",), (50, 50, "$50", "$25"), (10, 99, "$99", "$89.10"))
    @ddt.unpack
    def test_eligible_eligible(self, discount_percentage, base_price, formatted_base_price, final_price):
        with patch.multiple(
            utils,
            can_receive_discount=Mock(return_value=True),
            get_course_prices=Mock(return_value=(base_price, None)),
            discount_percentage=Mock(return_value=discount_percentage)
        ):
            content, has_discount = utils.format_strikeout_price(Mock(name='user'), Mock(name='course'))

        assert six.text_type(content) == (
            u"<span class='sr-only'>"
            u"Original price: <span class='price original'>{original_price}</span>, discount price: "
            u"</span>"
            u"<span class='price discount'>{discount_price}</span> "
            u"<del aria-hidden='true'><span class='price original'>{original_price}</span></del>"
        ).format(original_price=formatted_base_price, discount_price=final_price)
        assert has_discount
