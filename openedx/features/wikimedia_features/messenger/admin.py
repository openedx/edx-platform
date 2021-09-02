"""
Admin registration for Messenger.
"""
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from openedx.features.wikimedia_features.messenger.models import (
   Message, Inbox
)


class MessageAdmin(admin.ModelAdmin):
    """
    Admin config clearesult credit providers.
    """
    search_fields = ('sender__username', 'receiver__username')
    list_display = ('id', 'sender', 'receiver', 'message', 'created')


class InboxAdmin(admin.ModelAdmin):
    """
    Admin config for clearesult credits offered by the courses.
    """
    search_fields = ('sender', 'receiver')
    list_display = ('id', 'sender', 'receiver', 'message', 'unread_count')

    def sender(self, obj):
        return obj.last_message.sender.username

    def receiver(self, obj):
        return obj.last_message.receiver.username

    def message(self, obj):
        return obj.last_message.message[:20]


admin.site.register(Message, MessageAdmin)
admin.site.register(Inbox, InboxAdmin)
