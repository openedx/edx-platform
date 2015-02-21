"""
Django admin page for embargo models
"""
from django.contrib import admin
import textwrap

from config_models.admin import ConfigurationModelAdmin
from embargo.models import IPFilter, CountryAccessRule, RestrictedCourse
from embargo.forms import IPFilterForm, RestrictedCourseForm


class IPFilterAdmin(ConfigurationModelAdmin):
    """Admin for blacklisting/whitelisting specific IP addresses"""
    form = IPFilterForm
    fieldsets = (
        (None, {
            'fields': ('enabled', 'whitelist', 'blacklist'),
            'description': textwrap.dedent("""Enter specific IP addresses to explicitly
            whitelist (not block) or blacklist (block) in the appropriate box below.
            Separate IP addresses with a comma. Do not surround with quotes.
            """)
        }),
    )


class CountryAccessRuleInline(admin.StackedInline):
    """Inline editor for country access rules. """
    model = CountryAccessRule
    extra = 1

    def has_delete_permission(self, request, obj=None):
        return True


class RestrictedCourseAdmin(admin.ModelAdmin):
    """Admin for configuring course restrictions. """
    inlines = [CountryAccessRuleInline]
    form = RestrictedCourseForm


admin.site.register(IPFilter, IPFilterAdmin)
admin.site.register(RestrictedCourse, RestrictedCourseAdmin)
