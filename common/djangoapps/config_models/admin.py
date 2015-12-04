"""
Admin site models for managing :class:`.ConfigurationModel` subclasses
"""

from django.forms import models
from django.contrib import admin
from django.contrib.admin import ListFilter
from django.core.cache import get_cache, InvalidCacheBackendError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

try:
    cache = get_cache('configuration')  # pylint: disable=invalid-name
except InvalidCacheBackendError:
    from django.core.cache import cache

# pylint: disable=protected-access


class ConfigurationModelAdmin(admin.ModelAdmin):
    """
    :class:`~django.contrib.admin.ModelAdmin` for :class:`.ConfigurationModel` subclasses
    """
    date_hierarchy = 'change_date'

    def get_actions(self, request):
        return {
            'revert': (ConfigurationModelAdmin.revert, 'revert', _('Revert to the selected configuration'))
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
        cache.delete(obj.cache_key_name(*(getattr(obj, key_name) for key_name in obj.KEY_FIELDS)))
        cache.delete(obj.key_values_cache_key_name())

    def revert(self, request, queryset):
        """
        Admin action to revert a configuration back to the selected value
        """
        if queryset.count() != 1:
            self.message_user(request, _("Please select a single configuration to revert to."))
            return

        target = queryset[0]
        target.id = None
        self.save_model(request, target, None, False)
        self.message_user(request, _("Reverted configuration."))

        return HttpResponseRedirect(
            reverse(
                'admin:{}_{}_change'.format(
                    self.model._meta.app_label,
                    self.model._meta.module_name,
                ),
                args=(target.id,),
            )
        )


class ShowHistoryFilter(ListFilter):
    """
    Admin change view filter to show only the most recent (i.e. the "current") row for each
    unique key value.
    """
    title = _('Status')
    parameter_name = 'show_history'

    def __init__(self, request, params, model, model_admin):
        super(ShowHistoryFilter, self).__init__(request, params, model, model_admin)
        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            self.used_parameters[self.parameter_name] = value

    def has_output(self):
        """ Should this filter be shown? """
        return True

    def choices(self, cl):
        """ Returns choices ready to be output in the template. """
        show_all = self.used_parameters.get(self.parameter_name) == "1"
        return (
            {
                'display': _('Current Configuration'),
                'selected': not show_all,
                'query_string': cl.get_query_string({}, [self.parameter_name]),
            },
            {
                'display': _('All (Show History)'),
                'selected': show_all,
                'query_string': cl.get_query_string({self.parameter_name: "1"}, []),
            }
        )

    def queryset(self, request, queryset):
        """ Filter the queryset. No-op since it's done by KeyedConfigurationModelAdmin """
        return queryset

    def expected_parameters(self):
        """ List the query string params used by this filter """
        return [self.parameter_name]


class KeyedConfigurationModelAdmin(ConfigurationModelAdmin):
    """
    :class:`~django.contrib.admin.ModelAdmin` for :class:`.ConfigurationModel` subclasses that
    use extra keys (i.e. they have KEY_FIELDS set).
    """
    date_hierarchy = None
    list_filter = (ShowHistoryFilter, )

    def queryset(self, request):
        """
        Annote the queryset with an 'is_active' property that's true iff that row is the most
        recently added row for that particular set of KEY_FIELDS values.
        Filter the queryset to show only is_active rows by default.
        """
        if request.GET.get(ShowHistoryFilter.parameter_name) == '1':
            queryset = self.model.objects.with_active_flag()
        else:
            # Show only the most recent row for each key.
            queryset = self.model.objects.current_set()
        ordering = self.get_ordering(request)
        if ordering:
            return queryset.order_by(*ordering)
        return queryset

    def get_list_display(self, request):
        """ Add a link to each row for creating a new row using the chosen row as a template """
        return self.model._meta.get_all_field_names() + ['edit_link']

    def add_view(self, request, form_url='', extra_context=None):
        # Prepopulate new configuration entries with the value of the current config, if given:
        if 'source' in request.GET:
            get = request.GET.copy()
            source_id = int(get.pop('source')[0])
            source = get_object_or_404(self.model, pk=source_id)
            get.update(models.model_to_dict(source))
            request.GET = get
        # Call our grandparent's add_view, skipping the parent code
        # because the parent code has a different way to prepopulate new configuration entries
        # with the value of the latest config, which doesn't make sense for keyed models.
        # pylint: disable=bad-super-call
        return super(ConfigurationModelAdmin, self).add_view(request, form_url, extra_context)

    def edit_link(self, inst):
        """ Edit link for the change view """
        if not inst.is_active:
            return u'--'
        update_url = reverse('admin:{}_{}_add'.format(self.model._meta.app_label, self.model._meta.module_name))
        update_url += "?source={}".format(inst.pk)
        return u'<a href="{}">{}</a>'.format(update_url, _('Update'))
    edit_link.allow_tags = True
    edit_link.short_description = _('Update')
