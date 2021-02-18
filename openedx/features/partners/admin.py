from django.contrib import admin
from django.urls import reverse

from .models import Partner, PartnerCommunity, PartnerUser


class PartnerAdmin(admin.ModelAdmin):
    """
    Django admin customizations for Partner model
    """
    list_display = ('id', 'label', 'slug', 'partner_url')
    readonly_fields = ('partner_url',)

    def partner_url(self, obj):
        if obj.slug:
            return reverse('partner_url', kwargs={'slug': obj.slug})


class PartnerUserModelAdmin(admin.ModelAdmin):
    """
    Django admin to verify if user is affiliated with partner or not after login or registration
    """

    raw_id_fields = ('user',)


class PartnerCommunityModelAdmin(admin.ModelAdmin):
    """
    Django admin model to add community id to partner so that every user is added automatically to that community
    """
    list_display = ['id', 'partner', 'community_id']
    search_fields = ('partner', 'community_id')

    class Meta(object):
        verbose_name = 'Partner Community'
        verbose_name_plural = 'Partner Communities'


admin.site.register(Partner, PartnerAdmin)
admin.site.register(PartnerCommunity, PartnerCommunityModelAdmin)
admin.site.register(PartnerUser, PartnerUserModelAdmin)
