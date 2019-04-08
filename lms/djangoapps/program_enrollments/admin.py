# -*- coding: utf-8 -*-
"""
Admin tool for the Program Enrollments models
"""
from __future__ import unicode_literals

from django.contrib import admin

from lms.djangoapps.program_enrollments.models import ProgramEnrollment


class ProgramEnrollmentAdmin(admin.ModelAdmin):
    """
    Admin tool for the ProgramEnrollment model
    """

admin.site.register(ProgramEnrollment, ProgramEnrollmentAdmin)
