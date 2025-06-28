"""
Django admin for outline roots models
"""
from django.contrib import admin
from django.utils.safestring import SafeText

from openedx_learning.lib.admin_utils import ReadOnlyModelAdmin, model_detail_link

from .models import OutlineRoot


@admin.register(OutlineRoot)
class OutlineRootAdmin(ReadOnlyModelAdmin):
    """
    Very minimal interface... just direct the admin user's attention towards the related Container model admin.
    """
    list_display = ["outline_root_id", "key"]
    fields = ["see"]
    readonly_fields = ["see"]

    def outline_root_id(self, obj: OutlineRoot) -> int:
        return obj.pk

    def key(self, obj: OutlineRoot) -> SafeText:
        return model_detail_link(obj.container, obj.container.key)

    def see(self, obj: OutlineRoot) -> SafeText:
        return self.key(obj)