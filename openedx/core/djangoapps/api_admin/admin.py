"""Admin views for API managment."""
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from config_models.admin import ConfigurationModelAdmin
from openedx.core.djangoapps.api_admin.models import ApiAccessRequest, ApiAccessConfig


@admin.register(ApiAccessRequest)
class ApiAccessRequestAdmin(admin.ModelAdmin):
    """Admin for API access requests."""
    list_display = ('user', 'status', 'website')
    list_filter = ('status',)
    search_fields = ('user__email',)
    raw_id_fields = ('user',)
    readonly_fields = ('user', 'website', 'reason', 'company_name', 'company_address', 'contacted', )
    exclude = ('site',)

    def get_fieldsets(self, request, obj=None):
        return (
            (None, {
                'fields': (
                    'user', 'website', 'reason', 'company_name', 'company_address',
                )
            },),
            ('Status', {
                'description': _(
                    'Once you have approved this request, go to {catalog_admin_url} to set up a catalog for this user.'
                ).format(
                    catalog_admin_url='<a href="{0}">{0}</a>'.format(reverse('api_admin:catalog-search'))
                ),
                'fields': ('status',),
            }),
        )

admin.site.register(ApiAccessConfig, ConfigurationModelAdmin)
