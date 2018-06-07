"""
Admin for managing the connection to the Forums backend service.
"""
from config_models.admin import KeyedConfigurationModelAdmin
from django import forms
from django.contrib import admin

from .models import CourseForumsProfanityCheckerConfig, ForumsConfig


class ProfanityCheckerAdminForm(forms.ModelForm):
    """Input form for profanity checking configuration."""

    class Meta(object):
        model = CourseForumsProfanityCheckerConfig
        fields = '__all__'


class ProfanityCheckerConfigAdmin(KeyedConfigurationModelAdmin):
    """
    Admin for enabling forums profanity checking on a course-by-course basis.
    Allows searching by course id.
    """
    form = ProfanityCheckerAdminForm
    search_fields = ['course_id']
    fieldsets = (
        (None, {
            'fields': ('course_id', 'enabled', 'extra_bad_words', 'bad_word_patterns_to_ignore'),
            'description': 'Enter a valid course id.'
        }),
    )

admin.site.register(ForumsConfig)
admin.site.register(CourseForumsProfanityCheckerConfig, ProfanityCheckerConfigAdmin)
