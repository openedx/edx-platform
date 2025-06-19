"""Django admin interface for XBlock field data models."""
import json

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from openedx_learning.lib.admin_utils import ReadOnlyModelAdmin

from .models import XBlockVersionFieldData


@admin.register(XBlockVersionFieldData)
class XBlockVersionFieldDataAdmin(ReadOnlyModelAdmin):
    """
    Admin interface for XBlock field data records.
    """

    list_display = [
        'component',
        'version_num',
        'uuid',
        'created',
    ]

    fields = [
        'publishable_entity_version_link',
        'component_link',
        'version_num',
        'uuid',
        'created',
        'content_display',
        'settings_display',
    ]

    readonly_fields = fields

    def get_queryset(self, request):
        """Optimize queries by selecting related objects."""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'publishable_entity_version',
            'publishable_entity_version__componentversion',
            'publishable_entity_version__componentversion__component',
        )

    def component(self, obj):
        """Display the component key."""
        try:
            return obj.publishable_entity_version.componentversion.component.key
        except AttributeError:
            return "N/A"

    def version_num(self, obj):
        """Display the version number."""
        try:
            return obj.publishable_entity_version.version_num
        except AttributeError:
            return "N/A"

    def uuid(self, obj):
        """Display the UUID."""
        try:
            return obj.publishable_entity_version.uuid
        except AttributeError:
            return "N/A"

    def publishable_entity_version_link(self, obj):
        """Link to the related publishable entity version in admin."""
        admin_url = reverse('admin:oel_components_componentversion_change', args=[obj.publishable_entity_version.pk])
        return format_html('<a href="{}">{}</a>', admin_url, obj.publishable_entity_version)
    publishable_entity_version_link.short_description = "Publishable Entity Version"

    def component_link(self, obj):
        """Link to the related component in admin."""
        admin_url = reverse('admin:oel_components_component_change', args=[obj.publishable_entity_version.componentversion.component.pk])
        return format_html('<a href="{}">{}</a>', admin_url, obj.publishable_entity_version.componentversion.component)
    component_link.short_description = "Component"

    def content_display(self, obj):
        """Display formatted content fields."""
        if not obj.content:
            return "No content fields"

        return format_html(
            '<pre style="max-height: 600px; overflow-y: auto; white-space: pre-wrap;">{}</pre>',
            json.dumps(obj.content, indent=2),
        )
    content_display.short_description = "Content Fields"

    def settings_display(self, obj):
        """Display formatted settings fields."""
        if not obj.settings:
            return "No settings fields"

        return format_html(
            '<pre style="max-height: 600px; overflow-y: auto; white-space: pre-wrap;">{}</pre>',
            json.dumps(obj.settings, indent=2),
        )
    settings_display.short_description = "Settings Fields"
