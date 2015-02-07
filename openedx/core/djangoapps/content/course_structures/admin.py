import json

from ratelimitbackend import admin

from .models import CourseStructure

class CourseStructureAdmin(admin.ModelAdmin):
    search_fields = ('course_id', 'version')
    list_display = (
        'id', 'course_id', 'version', 'created'
    )
    list_display_links = ('id', 'course_id')

admin.site.register(CourseStructure, CourseStructureAdmin)
