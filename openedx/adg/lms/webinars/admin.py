"""
Registering models for webinars app.
"""
from django.contrib import admin
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from openedx.adg.lms.applications.admin import adg_admin_site

from .models import CancelledWebinar, Webinar, WebinarRegistration


class ActiveWebinarStatusFilter(admin.SimpleListFilter):
    """
    Custom filter to provide `Upcoming` and `Delivered` states filter functionality to the WebinarAdmin
    """

    title = _('Webinar Status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            (Webinar.UPCOMING, _('Upcoming')),
            (Webinar.DELIVERED, _('Delivered')),
        )

    def queryset(self, request, queryset):
        if self.value() == Webinar.UPCOMING:
            return queryset.filter(status=Webinar.UPCOMING)

        if self.value() == Webinar.DELIVERED:
            return queryset.filter(status=Webinar.DELIVERED)


class WebinarAdminBase(admin.ModelAdmin):
    """
    Base Model admin for webinars i.e Cancelled Webinars and Non-Cancelled Webinars
    """
    save_as = True
    list_display = ('title', 'start_time', 'presenter', 'status',)
    raw_id_fields = ('presenter', 'co_hosts', 'panelists')
    search_fields = ('title',)
    filter_horizontal = ('co_hosts', 'panelists',)


class WebinarAdmin(WebinarAdminBase):
    """
    Admin for upcoming and delivered webinars
    """
    list_filter = ('start_time', 'language', ActiveWebinarStatusFilter)
    readonly_fields = ('created_by', 'modified_by', 'status',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        else:
            obj.modified_by = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(WebinarAdmin, self).get_queryset(request)
        return qs.filter(~Q(status=Webinar.CANCELLED))


class CancelledWebinarAdmin(WebinarAdminBase):
    """
    Model admin for cancelled webinar
    """
    save_as = False

    def get_queryset(self, request):
        qs = super(CancelledWebinarAdmin, self).get_queryset(request)
        return qs.filter(status=Webinar.CANCELLED)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class WebinarRegistrationAdmin(admin.ModelAdmin):
    """
    Model admin for webinar registration
    """
    list_display = ('webinar', 'user', 'is_registered',)
    search_fields = ('webinar',)


admin.site.register(Webinar, WebinarAdmin)
adg_admin_site.register(Webinar, WebinarAdmin)

admin.site.register(CancelledWebinar, CancelledWebinarAdmin)
adg_admin_site.register(CancelledWebinar, CancelledWebinarAdmin)

admin.site.register(WebinarRegistration, WebinarRegistrationAdmin)
adg_admin_site.register(WebinarRegistration, WebinarRegistrationAdmin)
