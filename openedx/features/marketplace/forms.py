from django import forms

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
        readonly_fields = ('organization',)
