"""
Admin site bindings for contentstore
"""

import logging

from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.utils.translation import gettext as _
from edx_django_utils.admin.mixins import ReadOnlyAdminMixin

from cms.djangoapps.contentstore.models import (
    BackfillCourseTabsConfig,
    CleanStaleCertificateAvailabilityDatesConfig,
    VideoUploadConfig
)
from cms.djangoapps.contentstore.outlines_regenerate import CourseOutlineRegenerate
from openedx.core.djangoapps.content.learning_sequences.api import key_supports_outlines

from .tasks import update_outline_from_modulestore_task, update_all_outlines_from_modulestore_task


log = logging.getLogger(__name__)


def regenerate_course_outlines_subset(modeladmin, request, queryset):
    """
    Create a celery task to regenerate a single course outline for each passed-in course key.

    If the number of passed-in course keys is above a threshold, then instead create a celery task which
    will then create a celery task to regenerate a single course outline for each passed-in course key.
    """
    all_course_keys_qs = queryset.values_list('id', flat=True)

    # Create a separate celery task for each course outline requested.
    regenerates = 0
    for course_key in all_course_keys_qs:
        if key_supports_outlines(course_key):
            log.info("Queuing outline creation for %s", course_key)
            update_outline_from_modulestore_task.delay(str(course_key))
            regenerates += 1
        else:
            log.info("Outlines not supported for %s - skipping", course_key)
    msg = _("Number of course outline regenerations successfully requested: {regenerates}").format(
        regenerates=regenerates
    )
    modeladmin.message_user(request, msg)
regenerate_course_outlines_subset.short_description = _("Regenerate selected course outlines")


def regenerate_course_outlines_all(modeladmin, request, queryset):  # pylint: disable=unused-argument
    """
    Custom admin action which regenerates *all* the course outlines - no matter which CourseOverviews are selected.
    """
    update_all_outlines_from_modulestore_task.delay()
    modeladmin.message_user(request, _("All course outline regenerations successfully requested."))
regenerate_course_outlines_all.short_description = _("Regenerate *all* course outlines")


class CourseOutlineRegenerateAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """
    Regenerates the course outline for each selected course key.
    """
    list_display = ['id']
    ordering = ['id']
    search_fields = ['id']

    actions = [regenerate_course_outlines_subset, regenerate_course_outlines_all]

    def changelist_view(self, request, extra_context=None):
        """
        Overrides the admin's changelist_view & selects at least one of the CourseOverviews
        when the custom regenerate_course_outlines_all action is selected.
        """
        if 'action' in request.POST and request.POST['action'] == 'regenerate_course_outlines_all':
            # Slight hack: Ensure that at least one CourseOverview course key is selected.
            # The selection will be ignored, but the action will fail if *nothing* is selected.
            post = request.POST.copy()
            post.setlist(ACTION_CHECKBOX_NAME, self.model.get_course_outline_ids()[:1])
            request._set_post(post)  # pylint: disable=protected-access
        return super().changelist_view(request, extra_context)


class CleanStaleCertificateAvailabilityDatesConfigAdmin(ConfigurationModelAdmin):
    pass


admin.site.register(BackfillCourseTabsConfig, ConfigurationModelAdmin)
admin.site.register(VideoUploadConfig, ConfigurationModelAdmin)
admin.site.register(CourseOutlineRegenerate, CourseOutlineRegenerateAdmin)
admin.site.register(CleanStaleCertificateAvailabilityDatesConfig, ConfigurationModelAdmin)
