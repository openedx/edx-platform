"""
Django admin page for CourseOverviews, the basic metadata about a course that
is used in user dashboard queries and other places where you need info like
name, and start dates, but don't actually need to crawl into course content.
"""
from django.contrib import admin

from .models import CourseOverview


class CourseOverviewAdmin(admin.ModelAdmin):
    """
    Simple, read-only list/search view of Course Overviews.

    The detail view is broken because our primary key for this model are
    course keys, which can have a number of chars that break admin URLs.
    There's probably a way to make this work properly, but I don't have the
    time to investigate. I would normally disable the links by setting
    `list_display_links = None`, but that's not a valid value for that
    field in Django 1.4. So I'm left with creating a page where the detail
    view links are all broken for Split courses. Because I only created
    this page to manually test a hotfix, the list view works for this
    purpose, and that's all the yak I have time to shave today.
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


admin.site.register(CourseOverview, CourseOverviewAdmin)
