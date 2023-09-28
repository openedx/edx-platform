"""
Admin interface for LTI Provider app.
"""


from django.contrib import admin

from .models import LtiConsumer


class LtiConsumerAdmin(admin.ModelAdmin):
    """Admin for LTI Consumer"""
    search_fields = ('consumer_name', 'consumer_key', 'instance_guid')
    list_display = ('id', 'consumer_name', 'consumer_key', 'instance_guid')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return ("auto_link_users_using_email",)
        return super().get_readonly_fields(request, obj)


admin.site.register(LtiConsumer, LtiConsumerAdmin)
