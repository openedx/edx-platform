"""
Django admin page for CourseOverviews, the basic metadata about a course that
is used in user dashboard queries and other places where you need info like
name, and start dates, but don't actually need to crawl into course content.
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from .models import CourseOverview, CourseOverviewImageConfig, CourseOverviewImageSet, SimulateCoursePublishConfig


class CourseOverviewAdmin(admin.ModelAdmin):
    """
    Simple, read-only list/search view of Course Overviews.
    """
    list_display = [
        'id',
        'display_name',
        'version',
        'enrollment_start',
        'enrollment_end',
        'created',
        'modified',
    ]

    search_fields = ['id', 'display_name']


class CourseOverviewImageConfigAdmin(ConfigurationModelAdmin):
    """
    Basic configuration for CourseOverview Image thumbnails.

    By default this is disabled. If you change the dimensions of the images with
    a new config after thumbnails have already been generated, you need to clear
    the entries in CourseOverviewImageSet manually for new entries to be
    created.
    """
    list_display = [
        'change_date',
        'changed_by',
        'enabled',
        'large_width',
        'large_height',
        'small_width',
        'small_height'
    ]

    def get_list_display(self, request):
        """
        Restore default list_display behavior.

        ConfigurationModelAdmin overrides this, but in a way that doesn't
        respect the ordering. This lets us customize it the usual Django admin
        way.
        """
        return self.list_display


class CourseOverviewImageSetAdmin(admin.ModelAdmin):
    """
    Thumbnail images associated with CourseOverviews. This should be used for
    debugging purposes only -- e.g. don't edit these values.
    """
    list_display = [
        'course_overview',
        'small_url',
        'large_url',
    ]
    search_fields = ['course_overview__id']
    readonly_fields = ['course_overview_id']
    fields = ('course_overview_id', 'small_url', 'large_url')


class SimulateCoursePublishConfigAdmin(ConfigurationModelAdmin):
    pass


admin.site.register(CourseOverview, CourseOverviewAdmin)
admin.site.register(CourseOverviewImageConfig, CourseOverviewImageConfigAdmin)
admin.site.register(CourseOverviewImageSet, CourseOverviewImageSetAdmin)
admin.site.register(SimulateCoursePublishConfig, SimulateCoursePublishConfigAdmin)
