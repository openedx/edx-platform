"""
Django Admin for DisableProgressPageStackedConfig.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from openedx.core.djangoapps.config_model_utils.admin import StackedConfigModelAdmin

from .models import DisableProgressPageStackedConfig


class DisableProgressPageStackedConfigAdmin(StackedConfigModelAdmin):
    """
    Stacked Config Model Admin for disable the progress page
    """
    fieldsets = (
        ('Context', {
            'fields': DisableProgressPageStackedConfig.KEY_FIELDS,
            'description': _(
                'These define the context to disable the frontend-app-learning progress page.'
                'If no values are set, then the configuration applies globally. '
                'If a single value is set, then the configuration applies to all courses '
                'within that context. At most one value can be set at a time.<br>'
                'If multiple contexts apply to a course (for example, if configuration '
                'is specified for the course specifically, and for the org that the course '
                'is in, then the more specific context overrides the more general context.'
            ),
        }),
        ('Configuration', {
            'fields': ('disabled',),
            'description': _(
                'If any of these values is left empty or "Unknown", then their value '
                'at runtime will be retrieved from the next most specific context that applies. '
                'For example, if "Disabled" is left as "Unknown" in the course context, then that '
                'course will be Disabled only if the org that it is in is Disabled.'
            ),
        })
    )

admin.site.register(DisableProgressPageStackedConfig, DisableProgressPageStackedConfigAdmin)
