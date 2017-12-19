""" Form widget classes """

import django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms.utils import flatatt
from django.forms.widgets import CheckboxInput
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.translation import ugettext as _

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class TermsOfServiceCheckboxInput(CheckboxInput):
    """ Renders a checkbox with a label linking to the terms of service. """

    def render(self, name, value, attrs=None):
        # TODO: Remove Django 1.11 upgrade shim
        # SHIM: Compensate for behavior change of default authentication backend in 1.10
        if django.VERSION < (1, 11):
            final_attrs = self.build_attrs(attrs, type='checkbox', name=name)
        else:
            extra_attrs = attrs.copy()
            extra_attrs.update({'type': 'checkbox', 'name': name})
            final_attrs = self.build_attrs(self.attrs, extra_attrs=extra_attrs)  # pylint: disable=redundant-keyword-arg

        if self.check_test(value):
            final_attrs['checked'] = 'checked'
        if not (value is True or value is False or value is None or value == ''):
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_text(value)

        # Translators: link_start and link_end are HTML tags for a link to the terms of service.
        # platform_name is the name of this Open edX installation.
        label = _('I, and my company, accept the {link_start}{platform_name} API Terms of Service{link_end}.').format(
            platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
            link_start='<a href="{url}" target="_blank">'.format(url=reverse('api_admin:api-tos')),
            link_end='</a>',
        )

        html = u'<input{{}} /> <label class="tos-checkbox-label" for="{id}">{label}</label>'.format(
            id=final_attrs['id'],
            label=label
        )
        return format_html(html, flatatt(final_attrs))
