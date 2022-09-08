from django.contrib import admin
from openedx.features.genplus_features.genplus_badges.models import BoosterBadge, BoosterBadgeAward


@admin.register(BoosterBadge)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ('display_name', )
    list_display = (
        'slug',
        'skill',
        'display_name',
    )


@admin.register(BoosterBadgeAward)
class SkillAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'awarded_by',
        'badge',
    )
