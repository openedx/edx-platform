"""
Django admin page for waffle utils models
"""
from dal import autocomplete

from django.contrib import admin
from django.urls import path

from edx_toggles.toggles import WaffleFlag
from config_models.admin import KeyedConfigurationModelAdmin
from xmodule.modulestore.django import modulestore

from .forms import WaffleFlagCourseOverrideAdminForm, WaffleFlagOrgOverrideAdminForm
from .models import WaffleFlagCourseOverrideModel, WaffleFlagOrgOverrideModel


class CourseIDAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        all_course_ids = [str(course.id) for course in modulestore().get_courses()]
        if self.q:
            return [cid for cid in all_course_ids if self.q.lower() in cid.lower()]
        return all_course_ids


class WaffleFlagAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        flags = [w.name for w in WaffleFlag.get_instances()]
        if self.q:
            return [f for f in flags if self.q.lower() in f.lower()]
        return flags


class WaffleFlagCourseOverrideAdmin(KeyedConfigurationModelAdmin):
    """
    Admin for course override of waffle flags.

    Includes search by course_id and waffle_flag.

    """
    form = WaffleFlagCourseOverrideAdminForm
    search_fields = ['waffle_flag', 'course_id']
    fieldsets = (
        (None, {
            'fields': ('waffle_flag', 'course_id', 'note', 'override_choice', 'enabled'),
            'description':
                'Enter a valid course id and an existing waffle flag. The waffle flag name is not validated.'
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'waffle-flag-autocomplete/',
                WaffleFlagAutocomplete.as_view(),
                name='waffle-flag-autocomplete'
            ),
            path(
                'course-id-autocomplete/',
                CourseIDAutocomplete.as_view(),
                name='course-id-autocomplete'
            ),
        ]
        return custom_urls + urls


class WaffleFlagOrgOverrideAdmin(KeyedConfigurationModelAdmin):
    """
    Admin for org override of waffle flags.

    Includes search by org and waffle_flag.

    """
    form = WaffleFlagOrgOverrideAdminForm
    search_fields = ['waffle_flag', 'org']
    fieldsets = (
        (None, {
            'fields': ('waffle_flag', 'org', 'note', 'override_choice', 'enabled'),
            'description':
                'Enter a valid organization and an existing waffle flag. The waffle flag name is not validated.'
        }),
    )

admin.site.register(WaffleFlagCourseOverrideModel, WaffleFlagCourseOverrideAdmin)
admin.site.register(WaffleFlagOrgOverrideModel, WaffleFlagOrgOverrideAdmin)
