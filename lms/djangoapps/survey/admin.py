"""
Provide accessors to these models via the Django Admin pages
"""

from django import forms
from django.contrib import admin
from survey.models import SurveyForm


class SurveyFormAdminForm(forms.ModelForm):  # pylint: disable=R0924
    """Form providing validation of SurveyForm content."""

    class Meta:  # pylint: disable=C0111
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
