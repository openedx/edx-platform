from django.contrib import admin

from models import DiscussionCommunityMembership


class DiscussionCommunityMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'community', 'get_course')
    raw_id_fields = ('user',)

    def get_course(self, obj):
        return obj.community.course_id

    get_course.short_description = 'course id'
    get_course.admin_order_field = 'community__course_id'


admin.site.register(DiscussionCommunityMembership, DiscussionCommunityMembershipAdmin)
