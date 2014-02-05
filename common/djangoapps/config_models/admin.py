"""
Admin site models for managing :class:`.ConfigurationModel` subclasses
"""

from django.forms import models
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

# pylint: disable=protected-access


class ConfigurationModelAdmin(admin.ModelAdmin):
    """
    :class:`~django.contrib.admin.ModelAdmin` for :class:`.ConfigurationModel` subclasses
    """
    date_hierarchy = 'change_date'

    def get_actions(self, request):
        return {
            'revert': (ConfigurationModelAdmin.revert, 'revert', 'Revert to the selected configuration')
        }

    def get_list_display(self, request):
        return self.model._meta.get_all_field_names()

    # Don't allow deletion of configuration
    def has_delete_permission(self, request, obj=None):
        return False

    # Make all fields read-only when editing an object
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.model._meta.get_all_field_names()
        return self.readonly_fields

    def add_view(self, request, form_url='', extra_context=None):
        # Prepopulate new configuration entries with the value of the current config
        get = request.GET.copy()
        get.update(models.model_to_dict(self.model.current()))
        request.GET = get
        return super(ConfigurationModelAdmin, self).add_view(request, form_url, extra_context)

    # Hide the save buttons in the change view
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['readonly'] = True
        return super(ConfigurationModelAdmin, self).change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context
        )

    def save_model(self, request, obj, form, change):
        obj.changed_by = request.user
        super(ConfigurationModelAdmin, self).save_model(request, obj, form, change)

    def revert(self, request, queryset):
        """
        Admin action to revert a configuration back to the selected value
        """
        if queryset.count() != 1:
            self.message_user(request, "Please select a single configuration to revert to.")
            return

        target = queryset[0]
        target.id = None
        self.save_model(request, target, None, False)
        self.message_user(request, "Reverted configuration.")

        return HttpResponseRedirect(
            reverse(
                'admin:{}_{}_change'.format(
                    self.model._meta.app_label,
                    self.model._meta.module_name,
                ),
                args=(target.id,),
            )
        )
