"""
Admin configurations for Job Board app
"""
from django.contrib import admin

from .models import Job


class JobModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'type', 'compensation', 'hours', 'city', 'country')


admin.site.register(Job, JobModelAdmin)
