"""
Defines a form for providing validation of subsection grade templates.
"""

from django import forms

from openedx.core.lib.courses import clean_course_id

from .models import WaffleFlagCourseOverrideModel


class WaffleFlagCourseOverrideAdminForm(forms.ModelForm):
    """
    Input form for course override of waffle flags, allowing us to verify data.
    """
    class Meta(object):
        model = WaffleFlagCourseOverrideModel
        fields = '__all__'

    def clean_course_id(self):
        """
        Validate the course id
        """
        return clean_course_id(self)

    def clean_waffle_flag(self):
        """
        Validate the waffle flag is an existing flag.
        """
        cleaned_flag = self.cleaned_data['waffle_flag']

        if not cleaned_flag:
            msg = u'Waffle flag must be supplied.'
            raise forms.ValidationError(msg)

        return cleaned_flag.strip()
