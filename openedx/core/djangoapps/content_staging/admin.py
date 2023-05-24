"""
Admin views for Staged Content and Clipboard
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import StagedContent, UserClipboard


@admin.register(StagedContent)
class StagedContentAdmin(admin.ModelAdmin):
    """ Admin config for StagedContent """
    list_display = ('id', 'user', 'created', 'purpose', 'status', 'block_type', 'display_name', 'suggested_url_name')
    list_filter = ('purpose', 'status', 'block_type')
    search_fields = ('user__username', 'display_name', 'suggested_url_name')
    readonly_fields = ('id', 'user', 'created', 'purpose', 'status', 'block_type', 'olx')


@admin.register(UserClipboard)
class UserClipboardAdmin(admin.ModelAdmin):
    """ Admin config for UserClipboard """
    list_display = ('user', 'content_link', 'source_usage_key', 'get_source_context_title')
    search_fields = ('user__username', 'source_usage_key', 'content__display_name')
    readonly_fields = ('source_context_key', 'get_source_context_title')

    def content_link(self, obj):
        """ Display the StagedContent object as a link """
        url = reverse('admin:content_staging_stagedcontent_change', args=[obj.content.pk])
        return format_html('<a href="{}">{}</a>', url, obj.content)
    content_link.short_description = 'Content'

    def get_source_context_title(self, obj):
        return obj.get_source_context_title()
    get_source_context_title.short_description = 'Source Context Title'
