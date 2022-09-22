from django.contrib import admin
from openedx.features.genplus_features.genplus_badges.models import (BoosterBadge,
                                                                     BoosterBadgeAward,
                                                                     BoosterBadgeType,
                                                                     )


@admin.register(BoosterBadge)
class BoosterBadgeAdmin(admin.ModelAdmin):
    search_fields = ('display_name',)
    list_display = (
        'slug',
        'type',
        'display_name',
    )


@admin.register(BoosterBadgeAward)
class BoosterBadgeAwardAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'awarded_by',
        'badge',
    )


@admin.register(BoosterBadgeType)
class BoosterBadgeType(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )
