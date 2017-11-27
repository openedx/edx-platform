"""
Django admin page for grades models
"""
from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lms.djangoapps.grades.config.forms import CoursePersistentGradesAdminForm
from lms.djangoapps.grades.config.models import (
    ComputeGradesSetting,
    CoursePersistentGradesFlag,
    PersistentGradesEnabledFlag
)
from lms.djangoapps.grades.models import PersistentSubsectionGradeOverride, PersistentSubsectionGrade


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


class PersistentSubsectionGradeOverrideAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'grade',
                'earned_all_override',
                'earned_graded_override',
                'possible_all_override',
                'possible_graded_override',
            ),
            'description': 'Enter the ID of the subsection grade you want to override. You will probably need to '
                           'find this in the read replica in the grades_persistentsubsectiongrade table.'
        }),
    )
    list_display = [
        'get_course_id',
        'get_usage_key',
        'get_user_id',
        'earned_all_override',
        'earned_graded_override',
        'created',
        'modified',
    ]
    list_filter = ('grade__course_id', 'grade__user_id',)
    raw_id_fields = ('grade',)
    search_fields = ['grade__course_id', 'grade__user_id', 'grade__usage_key']

    def get_course_id(self, persistent_grade):
        return persistent_grade.grade.course_id

    def get_usage_key(self, persistent_grade):
        return persistent_grade.grade.usage_key

    def get_user_id(self, persistent_grade):
        return persistent_grade.grade.user_id

    get_course_id.short_description = _('Course Id')
    get_usage_key.short_description = _('Usage Key')
    get_user_id.short_description = _('User Id')


admin.site.register(CoursePersistentGradesFlag, CoursePersistentGradesAdmin)
admin.site.register(PersistentGradesEnabledFlag, ConfigurationModelAdmin)
admin.site.register(ComputeGradesSetting, ConfigurationModelAdmin)
admin.site.register(PersistentSubsectionGradeOverride, PersistentSubsectionGradeOverrideAdmin)
