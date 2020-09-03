from django.contrib import admin

from .models import CompetencyAssessmentRecord, CourseEnrollmentMeta


class CompetencyAssessmentRecordModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)


class CourseEnrollmentMetaModelAdmin(admin.ModelAdmin):
    list_display = ('course_enrollment', 'program_uuid')
    raw_id_fields = ('course_enrollment',)


admin.site.register(CompetencyAssessmentRecord, CompetencyAssessmentRecordModelAdmin)
admin.site.register(CourseEnrollmentMeta, CourseEnrollmentMetaModelAdmin)
