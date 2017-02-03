"""
Django admin page for grades models
"""
from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin

from lms.djangoapps.grades.config.models import CoursePersistentGradesFlag, PersistentGradesEnabledFlag
from lms.djangoapps.grades.config.forms import CoursePersistentGradesAdminForm


class CoursePersistentGradesAdmin(KeyedConfigurationModelAdmin):
    """
    Admin for enabling subsection grades on a course-by-course basis.
    Allows searching by course id.
    """
    form = CoursePersistentGradesAdminForm
    search_fields = ['course_id']
    fieldsets = (
        (None, {
            'fields': ('course_id', 'enabled'),
            'description': 'Enter a valid course id. If it is invalid, an error message will display.'
        }),
    )

admin.site.register(CoursePersistentGradesFlag, CoursePersistentGradesAdmin)
admin.site.register(PersistentGradesEnabledFlag, ConfigurationModelAdmin)
