from django.contrib import admin
from django.urls import reverse

from .models import Partner


class PartnerAdmin(admin.ModelAdmin):
    """
    Django admin customizations for Partner model
    """
    list_display = ('id', 'label', 'slug', 'partner_url')
    readonly_fields = ('partner_url',)

    def partner_url(self, obj):
        if not hasattr(Partner, 'slug'):
            return

        return reverse('partner_url', kwargs={'slug': self.slug})


admin.site.register(Partner, PartnerAdmin)

