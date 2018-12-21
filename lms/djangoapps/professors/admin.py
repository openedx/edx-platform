# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from professors.models import Professor


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):

    search_fields = ('name',)

    list_display = (
        'id',
        'user',
        'name',
        'description',
        'is_active',
        'sort_num'
    )
