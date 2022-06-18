"""
Mixins for use in Django Admin classes.
"""


class ReadOnlyAdminMixin:
    """
    Disables all editing capabilities for the admin's model.
    An example usage: a Django proxy model which provides data to perform some other action.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display_links = None
        self.readonly_fields = [f.name for f in self.model._meta.get_fields()]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions["delete_selected"]  # pragma: no cover
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):  # pylint: disable=unused-argument
        return False

    def save_model(self, request, obj, form, change):
        pass  # pragma: no cover

    def delete_model(self, request, obj):
        pass  # pragma: no cover

    def save_related(self, request, form, formsets, change):
        pass  # pragma: no cover
