from django.contrib import admin
from .models import FxPrograms
admin.site.register(FxPrograms)
class FxPrograms(admin.ModelAdmin):
    list_display = ('name', 'program_id', 'courses_list', 'id_course_list')