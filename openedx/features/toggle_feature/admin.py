

from django.contrib import admin

from openedx.features.toggle_feature.models import (
	ToggleFeatureCourse ,
    ToggleFeatureUser
)

class ToggleFeatureCourseAdmin (admin.ModelAdmin):
    raw_id_fields = ("course",)
    list_display = ('course_id', 'is_discussion', 'is_feedback' , 'is_date_and_progress' , 'is_search' , 'is_chatGPT')

class ToggleFeatureUserAdmin (admin.ModelAdmin):
    list_display = ('student', 'is_discussion', 'is_feedback' , 'is_date_and_progress' , 'is_search' , 'is_chatGPT')

admin.site.register(ToggleFeatureCourse,ToggleFeatureCourseAdmin)
admin.site.register(ToggleFeatureUser, ToggleFeatureUserAdmin)