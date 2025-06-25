"""
Django admin for courses models
"""
from django.contrib import admin

from openedx_learning.lib.admin_utils import ReadOnlyModelAdmin

from .models import CatalogCourse, Course


@admin.register(CatalogCourse)
class CatalogCourseAdmin(ReadOnlyModelAdmin):
    """
    Django admin for CatalogCourse model
    """


@admin.register(Course)
class CourseAdmin(ReadOnlyModelAdmin):
    """
    Django admin for Course [Run] model
    """
