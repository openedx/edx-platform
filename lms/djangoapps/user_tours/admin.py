""" Django admin for User Tours. """

from django.contrib import admin

from lms.djangoapps.user_tours.models import UserTour


@admin.register(UserTour)
class UserTourAdmin(admin.ModelAdmin):
    """ Admin for UserTour. """
    list_display = ('user', 'course_home_tour_status', 'show_courseware_tour',)
    readonly_fields = ('user',)
    search_fields = ('user__username',)
