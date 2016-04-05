"""Forms for API management."""
from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _

from openedx.core.djangoapps.api_admin.models import ApiAccessRequest


class ApiAccessRequestForm(forms.ModelForm):
    """Form to request API access."""

    terms_of_service = forms.BooleanField(
        label=_('{platform_name} API Terms of Service').format(platform_name=settings.PLATFORM_NAME),
        help_text=_(
            'The resulting Package will still be considered part of Covered Code. Your Grants.'
            ' In consideration of, and distributed, a Modification is: (a) any addition to or loss'
            ' of data, programs or other fee is charged for the physical act of transferring a copy,'
            ' and you may do so by its licensors. The Licensor grants to You for damages, including '
            'any direct, indirect, special, incidental and consequential damages, such as lost profits;'
            ' iii) states that any such claim is resolved (such as deliberate and grossly negligent acts)'
            ' or agreed to in writing, the Copyright Holder nor by the laws of the Original Code and'
            ' any other entity based on the same media as an expression of character texts or the whole'
            ' of the Licensed Product, and (iv) you make to the general goal of allowing unrestricted '
            're-use and re-distribute applies to "Community Portal Server" and related software products'
            ' as well as in related documentation and collateral materials stating that you have modified'
            ' that component; or it may be copied, modified, distributed, and/or redistributed.'
        ),
    )

    class Meta(object):
        model = ApiAccessRequest
        fields = ('company_name', 'website', 'company_address', 'reason', 'terms_of_service')
        labels = {
            'reason': _('Describe what your application does.'),
        }
        help_texts = {
            'reason': None,
            'website': _("The URL of your company's website."),
            'company_name': _('The name of your company.'),
            'company_address': _('The contact address of your company.'),
        }
        widgets = {
            'company_address': forms.Textarea()
        }
