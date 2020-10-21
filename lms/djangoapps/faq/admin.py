from django.contrib import admin

from lms.djangoapps.faq.models import Faq


#@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    actions = ['disable', 'enable']
    fields = ('title', 'content',)
    list_display = ('title', 'content', 'created_at', 'added_by', 'updated_by', 'is_active',)

    def disable(self, request, queryset):
        queryset.update(is_active=False)

    disable.short_description = "Disable the selected pages"

    def enable(self, request, queryset):
        queryset.update(is_active=True)

    enable.short_description = "Enable the selected pages"

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.added_by = request.user
        else:
            obj.updated_by = request.user

        super(FaqAdmin, self).save_model(request, obj, form, change)
