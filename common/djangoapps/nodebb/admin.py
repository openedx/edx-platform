"""
Admin configuration for Discussion Community model.
"""
from django.contrib import admin

from common.djangoapps.nodebb.models import DiscussionCommunity


class DiscussionCommunityAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'community_url', )


admin.site.register(DiscussionCommunity, DiscussionCommunityAdmin)
