from django.contrib import admin
from .models import Job


class JobModel(admin.ModelAdmin):

    list_display = ('title', 'company', 'type', 'compensation', 'hours', 'city', 'country')


admin.site.register(Job, JobModel)
