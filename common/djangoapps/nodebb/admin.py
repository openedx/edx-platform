"""
Admin site for nodebb application.
"""
from django.contrib import admin

from nodebb.models import DiscussionCommunity


class DiscussionCommunityAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'community_url', )


admin.site.register(DiscussionCommunity, DiscussionCommunityAdmin)
