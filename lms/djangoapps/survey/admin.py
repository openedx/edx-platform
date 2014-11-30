"""
Provide accessors to these models via the Django Admin pages
"""

from django import forms
from django.contrib import admin
from survey.models import SurveyForm


class SurveyFormAdminForm(forms.ModelForm):  # pylint: disable=incomplete-protocol
    """Form providing validation of SurveyForm content."""

    class Meta:  # pylint: disable=missing-docstring
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
