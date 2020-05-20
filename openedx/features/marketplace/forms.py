from django import forms
from django.utils.translation import ugettext as _

from openedx.features.marketplace.models import MarketplaceRequest


class MarketplaceRequestForm(forms.ModelForm):
    def __init__(self,*args, **kwargs):
        super(MarketplaceRequestForm,self).__init__(*args, **kwargs)

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
            'organization': _('Organization Name*'),
            'organization_mission': _('Organization Mission*'),
            'organization_sector': _('Which sector is your organization working in?*'),
            'organizational_problems': _('Current Organizational Problems*'),
            'description': _('Brief Description of Challenges*'),
            'user_services': _('What help can you provide to other organizations?*'),
            'file': _('Additional Attachments (Optional)'),
            'image': _('Add Image'),
        }
        readonly_fields = ('organization',)
