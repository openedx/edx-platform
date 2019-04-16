# -*- coding: utf-8 -*-
"""
ProgramEnrollments Application Configuration
"""
from __future__ import unicode_literals

from django.apps import AppConfig


class ProgramEnrollmentsConfig(AppConfig):
    """
    Application configuration for ProgramEnrollment
    """
    name = 'lms.djangoapps.program_enrollments'

    plugin_app = {
        'url_config': {},
    }
