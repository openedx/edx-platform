from django import forms
from django.utils.translation import ugettext as _

from openedx.features.marketplace.models import MarketplaceRequest


class MarketplaceRequestForm(forms.ModelForm):
    class Meta:
        model = MarketplaceRequest
        fields = '__all__'
        widgets = {
            'user': forms.HiddenInput(),
            'organization': forms.Select(attrs={
                'style': 'pointer-events: none;'
            })
        }
        labels = {
            'organization': _('Organization Name'),
            'organization_mission': _('Organization Mission'),
        }
        readonly_fields = ('organization',)
