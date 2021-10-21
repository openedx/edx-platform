"""
Django Admin pages for Course Rating.
"""

from django.contrib import admin

from openedx.features.course_rating.models import CourseRating, CourseAverageRating


class CourseRatingAdmin(admin.ModelAdmin):
    """
    Admin interface for the "CourseRating" object.
    """
    search_fields = ['user', 'course', 'rating', 'comment', 'is_approved', 'moderated_by']
    list_display = ['username', 'course', 'rating', 'is_approved', 'moderated_by', 'comment']

    def username(self, obj):
        return obj.user.username


class CourseAverageRatingAdmin(admin.ModelAdmin):
    """
    Admin interface for the "CourseAverageRating" object.
    """
    search_fields = ['course', 'average_rating', 'total_raters']
    list_display = ['course', 'average_rating', 'total_raters']


admin.site.register(CourseRating, CourseRatingAdmin)
admin.site.register(CourseAverageRating, CourseAverageRatingAdmin)
