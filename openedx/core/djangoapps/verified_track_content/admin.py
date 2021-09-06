"""
Django admin page for verified track configuration
"""


from django.contrib import admin

from openedx.core.djangoapps.verified_track_content.forms import VerifiedTrackCourseForm
from openedx.core.djangoapps.verified_track_content.models import (
    MigrateVerifiedTrackCohortsSetting,
    VerifiedTrackCohortedCourse
)


@admin.register(VerifiedTrackCohortedCourse)
class VerifiedTrackCohortedCourseAdmin(admin.ModelAdmin):
    """Admin for enabling verified track cohorting. """
    form = VerifiedTrackCourseForm


@admin.register(MigrateVerifiedTrackCohortsSetting)
class MigrateVerifiedTrackCohortsSettingAdmin(admin.ModelAdmin):
    """Admin for configuring migration settings of verified track cohorting"""
