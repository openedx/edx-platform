"""
Admin interface for LTI Provider app.
"""


from django.contrib import admin

from .models import LtiConsumer


@admin.register(LtiConsumer)
class LtiConsumerAdmin(admin.ModelAdmin):
    """Admin for LTI Consumer"""
    search_fields = ('consumer_name', 'consumer_key', 'instance_guid')
    list_display = ('id', 'consumer_name', 'consumer_key', 'instance_guid')

