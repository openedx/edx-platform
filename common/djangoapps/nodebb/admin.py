from django.contrib import admin

from models import DiscussionCommunity


class DiscussionCommunityAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'community_url', )


admin.site.register(DiscussionCommunity, DiscussionCommunityAdmin)
