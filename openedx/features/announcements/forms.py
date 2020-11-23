"""
Forms for the Announcement Editor
"""


from django import forms

from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    """
    Form for editing Announcements
    """
    content = forms.CharField(widget=forms.Textarea, label='', required=False)
    active = forms.BooleanField(initial=True, required=False)

    class Meta:
        model = Announcement
        fields = ['content', 'active']
