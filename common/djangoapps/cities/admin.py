from django.contrib import admin
from models import *

class CityAdmin(admin.ModelAdmin):
    ordering = ['code']
    search_fields = ['code', 'name']

admin.site.register(City, CityAdmin)

