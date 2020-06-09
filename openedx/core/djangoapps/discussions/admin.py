from django.contrib import admin

from .models import DiscussionProviderConfig, LearningContextDiscussionConfig


class DiscussionProviderConfigAdminModel(admin.ModelAdmin):
    search_fields = ("name", "provider", "config")
    list_filter = ("restrict_to_site", "restrict_to_org", "provider")


admin.site.register(DiscussionProviderConfig, DiscussionProviderConfigAdminModel)
admin.site.register(LearningContextDiscussionConfig)
