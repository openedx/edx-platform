# -*- coding: utf-8 -*-
"""
Django Admin pages for ContentTypeGatingConfig.
"""

from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.config_model_utils.admin import StackedConfigModelAdmin
from .models import ContentTypeGatingConfig


class ContentTypeGatingConfigAdmin(StackedConfigModelAdmin):
    fieldsets = (
        ('Context', {
            'fields': ('site', 'org', 'course'),
            'description': _(
                'These define the context to enable course duration limits on. '
                'If no values are set, then the configuration applies globally. '
                'If a single value is set, then the configuration applies to all courses '
                'within that context. At most one value can be set at a time.<br>'
                'If multiple contexts apply to a course (for example, if configuration '
                'is specified for the course specifically, and for the org that the course '
                'is in, then the more specific context overrides the more general context.'
            ),
        }),
        ('Configuration', {
            'fields': ('enabled', 'enabled_as_of', 'studio_override_enabled'),
            'description': _(
                'If any of these values is left empty or "Unknown", then their value '
                'at runtime will be retrieved from the next most specific context that applies. '
                'For example, if "Enabled" is left as "Unknown" in the course context, then that '
                'course will be Enabled only if the org that it is in is Enabled.'
            ),
        })
    )
    raw_id_fields = ('course',)

admin.site.register(ContentTypeGatingConfig, ContentTypeGatingConfigAdmin)
