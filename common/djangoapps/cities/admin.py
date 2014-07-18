# -*- coding: utf-8 -*-
from django.contrib import admin
from models import *

class CityAdmin(admin.ModelAdmin):
    ordering = ['name', 'code']
    search_fields = ['code', 'name']

admin.site.register(City, CityAdmin)

class StateAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['code', 'name']

admin.site.register(State, StateAdmin)
