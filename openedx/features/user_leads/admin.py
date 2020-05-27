from django.contrib import admin

from openedx.features.user_leads.models import UserLeads


class LeadsModel(admin.ModelAdmin):
    list_display = (
        'user', 'utm_source', 'utm_content', 'utm_medium', 'utm_campaign', 'utm_term', 'date_created', 'origin'
    )
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)


admin.site.register(UserLeads, LeadsModel)
