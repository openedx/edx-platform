"""
Provide accessors to these models via the Django Admin pages
"""

from django.contrib import admin
from survey.models import SurveyForm


class SurveyFormAdmin(admin.ModelAdmin):
    """Admin for SurveyForm"""
    pass


admin.site.register(SurveyForm, SurveyFormAdmin)
