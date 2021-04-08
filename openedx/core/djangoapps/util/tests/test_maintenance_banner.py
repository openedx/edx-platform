"""
Tests for the view decorator which adds the maintenace banner.
"""


from unittest import mock

import ddt
from django.test import TestCase, override_settings
from edx_toggles.toggles.testutils import override_waffle_switch

from openedx.core.djangoapps.util.maintenance_banner import add_maintenance_banner as _add_maintenance_banner
from openedx.core.djangoapps.util.waffle import DISPLAY_MAINTENANCE_WARNING


@ddt.ddt
class TestMaintenanceBannerViewDecorator(TestCase):
    """
    Tests for view decorator which adds the maintenance banner.
    """

    def add_maintenance_banner(self):
        """
        Mock `add_maintenance_banner` that should be used for testing

        Returns tuple:
        (
            boolean to indicate if banner was added,
            string containing maintenance warning text,
        )
        """

        @_add_maintenance_banner
        def func(request):
            return request

        register_warning_message_path = (
            'openedx.core.djangoapps.util.maintenance_banner'
            '.PageLevelMessages.register_warning_message'
        )
        with mock.patch(register_warning_message_path) as mock_register_warning_message:
            func(request=mock.Mock())

            displayed_banner = mock_register_warning_message.called
            banner_text = None

            if displayed_banner:
                banner_text = mock_register_warning_message.call_args.args[1]

            return (displayed_banner, banner_text)

    @ddt.data(
        True,
        False,
    )
    def test_display_maintenance_warning_switch(self, display_warning):
        """
        Tests the `DISPLAY_MAINTENANCE_WARNING` switch is working as expected.

        Checks if the decorated request from `get_decorated_request` has a warning or not.
        """
        with override_waffle_switch(DISPLAY_MAINTENANCE_WARNING, active=display_warning):
            banner_added, _ = self.add_maintenance_banner()

            assert display_warning == banner_added

    @ddt.data(
        "If there's somethin' strange in your neighborhood, who ya gonna call?!"
    )
    @override_waffle_switch(DISPLAY_MAINTENANCE_WARNING, active=True)
    def test_maintenance_warning_text(self, warning_message):
        """
        Tests the `MAINTENANCE_BANNER_TEXT` is being set, as expected.

        Checks if the decorated request from `get_decorated_request` returns the specified warning message.
        """
        with override_settings(MAINTENANCE_BANNER_TEXT=warning_message):
            banner_added, banner_message = self.add_maintenance_banner()

            assert banner_added
            assert warning_message == banner_message
