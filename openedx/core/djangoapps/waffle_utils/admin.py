"""
Django admin page for waffle utils models
"""

from django.contrib import admin

from config_models.admin import KeyedConfigurationModelAdmin


from .forms import WaffleFlagCourseOverrideAdminForm
from .models import WaffleFlagCourseOverrideModel


class WaffleFlagCourseOverrideAdmin(KeyedConfigurationModelAdmin):
    """
    Admin for course override of waffle flags.

    Includes search by course_id and waffle_flag.

    """
    form = WaffleFlagCourseOverrideAdminForm
    search_fields = ['waffle_flag', 'course_id']
    fieldsets = (
        (None, {
            'fields': ('waffle_flag', 'course_id', 'override_choice', 'enabled'),
            'description': 'Enter a valid course id and an existing waffle flag. The waffle flag name is not validated.'
        }),
    )

admin.site.register(WaffleFlagCourseOverrideModel, WaffleFlagCourseOverrideAdmin)
