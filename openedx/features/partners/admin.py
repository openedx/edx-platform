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
        if obj.slug:
            return reverse('partner_url', kwargs={'slug': obj.slug})


admin.site.register(Partner, PartnerAdmin)

