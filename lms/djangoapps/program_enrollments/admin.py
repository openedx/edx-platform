# -*- coding: utf-8 -*-
"""
Admin tool for the Program Enrollments models
"""
from __future__ import unicode_literals

from django.contrib import admin

from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment


class ProgramEnrollmentAdmin(admin.ModelAdmin):
    """
    Admin tool for the ProgramEnrollment model
    """
    list_display = ('id', 'user', 'external_user_key', 'program_uuid', 'curriculum_uuid', 'status')
    list_filter = ('status',)
    raw_id_fields = ('user',)
    search_fields = ('user__username',)


class ProgramCourseEnrollmentAdmin(admin.ModelAdmin):
    """
    Admin tool for the ProgramCourseEnrollment model
    """
    list_display = ('id', 'program_enrollment', 'course_enrollment', 'course_key', 'status')
    list_filter = ('course_key',)
    raw_id_fields = ('program_enrollment', 'course_enrollment')


admin.site.register(ProgramEnrollment, ProgramEnrollmentAdmin)
admin.site.register(ProgramCourseEnrollment, ProgramCourseEnrollmentAdmin)
