"""
Provide accessors to these models via the Django Admin pages
"""


from django import forms
from django.contrib import admin

from lms.djangoapps.survey.models import SurveyForm


class SurveyFormAdminForm(forms.ModelForm):
    """Form providing validation of SurveyForm content."""

    class Meta:
        model = SurveyForm
        fields = ('name', 'form')

    def clean_form(self):
        """Validate the HTML template."""
        form = self.cleaned_data["form"]
        SurveyForm.validate_form_html(form)
        return form


class SurveyFormAdmin(admin.ModelAdmin):
    """Admin for SurveyForm"""
    form = SurveyFormAdminForm


admin.site.register(SurveyForm, SurveyFormAdmin)
