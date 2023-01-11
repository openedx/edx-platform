from math import floor

from django.conf import settings
from edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.mobile_utils import is_request_from_mobile_app

DEFAULT_SERVICES_NOTIFICATIONS_COOKIE_EXPIRY = 180  # value in seconds
DEFAULT_COLOR_DICT = {
    'primary': '#3E99D4',
    'secondary': '#1197EA'
}
DEFAULT_FONTS_DICT = {
    'base-font': "'Open Sans', sans-serif",
    'heading-font': "'Open Sans', sans-serif",
    'font-path': "https://fonts.googleapis.com/css?family=Open+Sans:400,600,700&display=swap",
}
DEFAULT_BRANDING_DICT = {
    'logo': "https://edly-edx-theme-files.s3.amazonaws.com/st-lutherx-logo.png",
    'favicon': "https://edly-edx-theme-files.s3.amazonaws.com/favicon.ico",
}


def dynamic_theming_context(request):  # pylint: disable=unused-argument
    """
    Context processor responsible for dynamic theming.
    """
    theming_context = {}
    theming_context.update(
        {'edly_colors_config': get_theme_colors()}
    )
    theming_context.update(
        {'edly_fonts_config': configuration_helpers.get_dict('FONTS', DEFAULT_FONTS_DICT)}
    )
    theming_context.update(
        {'edly_branding_config': configuration_helpers.get_dict('BRANDING', DEFAULT_BRANDING_DICT)}
    )

    return theming_context


def edly_app_context(request):  # pylint: disable=unused-argument
    """
    Context processor responsible for edly.
    """
    edly_context = {}
    panel_services_notifications_url = ''

    panel_notifications_base_url = configuration_helpers.get_value('PANEL_NOTIFICATIONS_BASE_URL', '')
    if panel_notifications_base_url:
        panel_services_notifications_url = '{base_url}/api/v1/all_services_notifications/'.format(
            base_url=panel_notifications_base_url
        )

    edly_context.update(
        {
            'edly_copyright_text': configuration_helpers.get_value('EDLY_COPYRIGHT_TEXT'),
            'services_notifications_url': panel_services_notifications_url,
            'session_cookie_domain': configuration_helpers.get_value(
                'SESSION_COOKIE_DOMAIN', settings.SESSION_COOKIE_DOMAIN
            ),
            'services_notifications_cookie_expiry': configuration_helpers.get_value(
                'SERVICES_NOTIFICATIONS_COOKIE_EXPIRY', DEFAULT_SERVICES_NOTIFICATIONS_COOKIE_EXPIRY
            ),
            'nav_menu_url': marketing_link('NAV_MENU'),
            'zendesk_widget_url': marketing_link('ZENDESK-WIDGET'),
            'footer_url': marketing_link('FOOTER'),
            'gtm_id': configuration_helpers.get_value('GTM_ID'),
            'ga_id': configuration_helpers.get_value('GA_ID'),
            'hotjar_id': settings.HOTJAR_TRACKING_ID,
            'usetiful_token': settings.USETIFUL_TOKEN,
            'is_mobile_app': is_request_from_mobile_app(request)
        }
    )

    return edly_context


def get_theme_colors():
    color_dict = configuration_helpers.get_dict('COLORS', DEFAULT_COLOR_DICT)
    primary = Colour(str(color_dict.get('primary')))
    secondary = Colour(str(color_dict.get('secondary')))

    primary_hover = color_dict.get('primary-hover')
    primary_rgb = color_dict.get('primary-rgb')
    primary_lighten_5p = color_dict.get('primary-lighten-5p')
    primary_lighten_10p = color_dict.get('primary-lighten-10p')
    primary_darken_5p = color_dict.get('primary-darken-5p')
    primary_darken_10p = color_dict.get('primary-darken-10p')

    secondary_hover = color_dict.get('secondary-hover')
    secondary_rgb = color_dict.get('secondary-rgb')
    secondary_lighten_5p = color_dict.get('secondary-lighten-5p')
    secondary_lighten_10p = color_dict.get('secondary-lighten-10p')
    secondary_darken_5p = color_dict.get('secondary-darken-5p')
    secondary_darken_10p = color_dict.get('secondary-darken-10p')

    colours = {
        'primary': color_dict.get('primary'),
        'secondary': color_dict.get('secondary'),
        'primary-hover': get_hover_color(primary_hover, primary),
        'primary-rgb': get_rgb_color(primary_rgb, primary),
        'primary-lighten-5p': get_lighten_color(primary_lighten_5p, primary, 0.05),
        'primary-lighten-10p': get_lighten_color(primary_lighten_10p, primary, 0.1),
        'primary-darken-5p': get_darken_color(primary_darken_5p, primary, 0.05),
        'primary-darken-10p': get_darken_color(primary_darken_10p, primary, 0.1),
        'secondary-hover': get_hover_color(secondary_hover, secondary),
        'secondary-rgb': get_rgb_color(secondary_rgb, secondary),
        'secondary-lighten-5p': get_lighten_color(secondary_lighten_5p, secondary, 0.05),
        'secondary-lighten-10p': get_lighten_color(secondary_lighten_10p, secondary, 0.1),
        'secondary-darken-5p': get_darken_color(secondary_darken_5p, secondary, 0.05),
        'secondary-darken-10p': get_darken_color(secondary_darken_10p, secondary, 0.1),
    }

    return colours


def get_hover_color(color_string, color_object):
    return color_string if color_string else get_darken_color('', color_object, 0.5)


def get_lighten_color(color_string, color_object, scale):
    return color_string if color_string else color_object.lighten(scale).hex


def get_darken_color(color_string, color_object, scale):
    return color_string if color_string else color_object.darken(scale).hex


def get_rgb_color(color_string, color_object):
    return color_string if color_string else ','.join([str(i) for i in color_object.rgb])


class Colour(object):
    def __init__(self, *args):
        """
        Parse the initialising argument(s):

        The arguments might be:
            - three integers corresponding to RGB values out of 255
            - an RGB tuple or list
            - a greyscale percentage
            - greyscale value out of 255
            - a 3 digit hexadecimal string
            - or a 6 digit hexadecimal string
        """

        def _colour_convert():
            """
            Post-process parsed red, green and blue values into hex
            """
            r = self.red
            g = self.green
            b = self.blue
            self.hex = '#' + format(int(floor(r)), '02X') + format(int(floor(g)), '02X') + format(int(floor(b)), '02X')
            self.rgb = (r, g, b)
            _hue_convert()

        def _validate_and_parse_rgb_arguments(args):
            if (max(args) > 255) or (min(args) < 0):
                raise ValueError('RGB values must be between 0 and 255')

            self.red, self.green, self.blue = args
            _colour_convert()

        def _validate_gray_scale_input(args):
            if args[0] < 0 or args[0] > 255:
                raise ValueError('Greyscale value must be either out of 1 or 255')
            if args[0] <= 1:
                self.red = self.green = self.blue = args[0] * 255
            else:
                self.red = self.green = self.blue = args[0]
            _colour_convert()

        def _validate_hex_input(args):
            string = args[0]
            if len(string) in [4, 7] and string[0] == '#':
                string = string[1:]

            hexerror = "Hex string must be in the form 'RGB', '#RGB', 'RRGGBB'" \
                       " or '#RRGGBB', and each digit must be a valid hexadecimal digit"
            if len(string) not in [3, 6]:
                raise TypeError(hexerror)

            if len(string) == 3:
                try:
                    self.red = int(string[0], 16) * 17
                    self.green = int(string[1], 16) * 17
                    self.blue = int(string[2], 16) * 17
                except ValueError:
                    raise ValueError(hexerror + '3')
            elif len(string) == 6:
                try:
                    self.red = int(string[0:2], 16)
                    self.green = int(string[2:4], 16)
                    self.blue = int(string[4:6], 16)
                except ValueError:
                    raise ValueError(hexerror + '6')
            _colour_convert()

        def _calculate_lightness_values(max_rgb, min_rgb, red, green, blue):
            return (max_rgb + min_rgb) / 2., max_rgb, (red + green + blue) / 3.

        def _calculate_saturation_values(hue, rgb_difference, min_rgb, lightness, value, intensity):
            if rgb_difference == 0:
                hue_saturation_lightness = hue_saturation_value = hue_saturation_intensity = 0
            else:
                hue_saturation_lightness = rgb_difference / (1 - abs((2 * lightness) - 1))
                hue_saturation_value = rgb_difference / value
                hue_saturation_intensity = 1 - (float(min_rgb) / intensity)

            self.hsl = (hue, hue_saturation_lightness, lightness)
            self.hsv = (hue, hue_saturation_value, value)
            self.hsi = (hue, hue_saturation_intensity, intensity)

        def _hue_convert():
            """
            Calculates hue saturation value, intensity, lightness.

            HSV: hue saturation value
            HSI: hue saturation intensity
            HSL: hue saturation lightness
            """
            red = self.red / 255.
            green = self.green / 255.
            blue = self.blue / 255.
            max_rgb = max(red, green, blue)
            min_rgb = min(red, green, blue)
            rgb_difference = float(max_rgb - min_rgb)
            if rgb_difference == 0:
                hue = 0
            elif max_rgb == red:
                hue = ((green - blue) / rgb_difference) % 6
            elif max_rgb == green:
                hue = ((blue - red) / rgb_difference) + 2
            elif max_rgb == blue:
                hue = ((red - green) / rgb_difference) + 4

            hue *= 60
            self.hue = hue
            lightness, value, intensity = _calculate_lightness_values(max_rgb, min_rgb, red, green, blue)
            _calculate_saturation_values(hue, rgb_difference, min_rgb, lightness, value, intensity)

        if len(args) == 1 and type(args[0]) in [tuple, list]:
            args = args[0]
        if len(args) == 3:
            _validate_and_parse_rgb_arguments(args)
        elif len(args) == 1 and type(args[0]) in [int, float, int]:
            _validate_gray_scale_input(args)
        elif len(args) == 1 and type(args[0]) == str:
            _validate_hex_input(args)
        else:
            raise TypeError(
                'Input arguments must either be 3 RGB values out'
                'of 255, a greyscale value out of either 1 or 255, or a hexadecimal string'
            )

    def __str__(self):
        return 'rgba' + self.__repr__()[6:]

    def __repr__(self):
        return 'Colour({},{},{})'.format(self.red, self.green, self.blue)

    def _trans(self, transparency, other_colored_background):
        """
        Returns a Colour object representing the colour when the calling
        colour has a transparency out of 1 against an other coloured
        background.
        """
        if transparency < 0 or transparency > 1:
            raise ValueError('Transparency must be between 0 and 1')

        red = (self.red * transparency) + (other_colored_background.red * (1 - transparency))
        green = (self.green * transparency) + (other_colored_background.green * (1 - transparency))
        blue = (self.blue * transparency) + (other_colored_background.blue * (1 - transparency))
        return Colour(red, green, blue)

    def lighten(self, lighten_factor):
        """
        Lighten the colour by provided lighten factor.
        """
        if lighten_factor < 0 or lighten_factor > 1:
            raise ValueError('Lighten factor must be between 0 and 1')

        return Colour('FFF')._trans(lighten_factor, self)

    def darken(self, darken_factor):
        """
        Darken the colour by provided darken factor.
        """
        if darken_factor < 0 or darken_factor > 1:
            raise ValueError('Darken factor must be between 0 and 1')

        return Colour('000')._trans(darken_factor, self)

    def trans(self, trans_factor):
        """
        Make the colour transparent by the provided transparent factor.
        """
        return self.darken(-1 * trans_factor) if trans_factor < 0 else self.lighten(trans_factor)
