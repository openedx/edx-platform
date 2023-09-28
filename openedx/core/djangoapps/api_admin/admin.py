"""Admin views for API managment."""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin
from django.urls import reverse
from django.utils.translation import gettext as _

from openedx.core.djangoapps.api_admin.models import ApiAccessConfig, ApiAccessRequest
from openedx.core.djangolib.markup import HTML, Text


@admin.register(ApiAccessRequest)
class ApiAccessRequestAdmin(admin.ModelAdmin):
    """Admin for API access requests."""
    list_display = ('user', 'status', 'website')
    list_filter = ('status',)
    search_fields = ('user__email',)
    raw_id_fields = ('user',)
    readonly_fields = ('user', 'email_address', 'website', 'reason', 'company_name', 'company_address', 'contacted',)
    exclude = ('site',)

    def email_address(self, obj):
        """User email requesting for API Access."""
        return obj.user.email

    def get_fieldsets(self, request, obj=None):
        return (
            (None, {
                'fields': (
                    'user', 'email_address', 'website', 'reason', 'company_name', 'company_address',
                )
            },),
            ('Status', {
                'description': Text(_(
                    'Once you have approved this request, go to {catalog_admin_url} to set up a catalog for this user.'
                )).format(
                    catalog_admin_url=HTML('<a href="{0}">{0}</a>').format(reverse('api_admin:catalog-search'))
                ),
                'fields': ('status',),
            }),
        )

admin.site.register(ApiAccessConfig, ConfigurationModelAdmin)
