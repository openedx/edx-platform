# -*- coding: utf-8 -*-
"""
Django Admin pages for DiscountRestrictionConfig.
"""


from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.config_model_utils.admin import StackedConfigModelAdmin

from .models import DiscountPercentageConfig, DiscountRestrictionConfig


class DiscountRestrictionConfigAdmin(StackedConfigModelAdmin):
    """
    Admin to configure discount restrictions
    """
    fieldsets = (
        ('Context', {
            'fields': DiscountRestrictionConfig.KEY_FIELDS,
            'description': _(
                'These define the context to disable lms-controlled discounts on. '
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
    raw_id_fields = ('course',)

admin.site.register(DiscountRestrictionConfig, DiscountRestrictionConfigAdmin)


class DiscountPercentageConfigAdmin(StackedConfigModelAdmin):
    """
    Admin to configure discount percentage
    """
    fieldsets = (
        ('Context', {
            'fields': DiscountRestrictionConfig.KEY_FIELDS,
            'description': _(
                'These define the context to configure the percentage for the first purchase discount.'
                'If multiple contexts apply to a course (for example, if configuration '
                'is specified for the course specifically, and for the org that the course '
                'is in, then the more specific context overrides the more general context.'
            ),
        }),
        ('Configuration', {
            'fields': ('percentage',),
        })
    )
    raw_id_fields = ('course',)

admin.site.register(DiscountPercentageConfig, DiscountPercentageConfigAdmin)
