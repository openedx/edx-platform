"""
Registering models for webinars app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.lms.applications.admin import adg_admin_site

from .constants import (
    SEND_UPDATE_EMAILS_FIELD,
    WEBINAR_REGISTRATION_DELETE_PERMISSION_GROUP,
    WEBINAR_STATUS_CANCELLED,
    WEBINAR_STATUS_DELIVERED,
    WEBINAR_STATUS_DRAFT,
    WEBINAR_STATUS_UPCOMING
)
from .forms import WebinarForm
from .helpers import (
    get_newly_added_and_removed_team_members,
    get_webinar_invitees_emails,
    remove_emails_duplicate_in_other_list,
    schedule_webinar_reminders,
    send_webinar_emails,
    webinar_emails_for_panelists_co_hosts_and_presenter
)
from .models import CancelledWebinar, Webinar, WebinarRegistration


class ActiveWebinarStatusFilter(admin.SimpleListFilter):
    """
    Custom filter to provide `Upcoming` and `Delivered` states filter functionality to the WebinarAdmin
    """

    title = _('Webinar Status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            (Webinar.UPCOMING, WEBINAR_STATUS_UPCOMING),
            (Webinar.DELIVERED, WEBINAR_STATUS_DELIVERED),
        )

    def queryset(self, request, queryset):
        if self.value() == Webinar.UPCOMING:
            return queryset.upcoming_webinars()

        if self.value() == Webinar.DELIVERED:
            return queryset.delivered_webinars()


class WebinarAdminBase(admin.ModelAdmin):
    """
    Base Model admin for webinars i.e Cancelled Webinars and Non-Cancelled Webinars
    """

    def webinar_status(self, webinar):
        """
        Method field to show webinar status.

        Args:
            webinar (Webinar): Current webinar object

        Returns:
            string: Webinar status either `Upcoming`, `Delivered`, `Cancelled` or `Draft`
        """
        is_published = getattr(webinar, 'is_published', False)
        if not is_published:
            return WEBINAR_STATUS_DRAFT

        if webinar.is_cancelled:
            return WEBINAR_STATUS_CANCELLED
        elif webinar and webinar.is_upcoming_webinar:
            return WEBINAR_STATUS_UPCOMING
        return WEBINAR_STATUS_DELIVERED

    save_as = True
    exclude = ('is_cancelled',)
    list_display = ('title', 'start_time', 'presenter', 'is_published', 'webinar_status',)
    raw_id_fields = ('presenter', 'co_hosts', 'panelists')
    search_fields = ('title',)
    filter_horizontal = ('co_hosts', 'panelists',)


class WebinarAdmin(WebinarAdminBase):
    """
    Admin for upcoming and delivered webinars
    """

    list_filter = ('start_time', 'language', 'is_published', ActiveWebinarStatusFilter)

    form = WebinarForm

    def __init__(self, model, admin_site):
        """
        Extend constructor to create instance variable for old webinar state to be stored in.

        When an existing webinar is updated, its old state is lost after the ModelAdmin's `save_model` method is
        executed. We want to store the old state before it is overridden so that it can be accessed in `save_related`
        method, which is executed after `save_model` method.
        """
        super().__init__(model, admin_site)
        self.old_webinar = None

    def get_fields(self, request, obj=None):
        """
        Override `get_fields` to dynamically set fields to be rendered.
        """
        fields = super().get_fields(request, obj)
        if not obj:
            fields.remove(SEND_UPDATE_EMAILS_FIELD)
        return fields

    def save_model(self, request, obj, form, change):
        """
        Extension of `save_model` to capture the old webinar state prior to updation
        """
        if change:
            self.old_webinar = Webinar.objects.get(id=obj.id)

        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        """
        Extension of `save_related` for webinar to send emails when a published webinar is created or modified.
        """
        new_members = []
        removed_members = []

        if (change and any(field in form.changed_data for field in ['co_hosts', 'presenter', 'panelists'])
                and form.instance.is_published):
            # The below method `get_newly_added_and_removed_team_members` must be called before
            # `super().save_related(...)` for correct results.
            new_members, removed_members = get_newly_added_and_removed_team_members(form, self.old_webinar)

        super().save_related(request, form, formsets, change)

        webinar = form.instance
        if not webinar.is_published:
            return

        webinar_invitees_emails = get_webinar_invitees_emails(form)

        is_previously_published = getattr(self.old_webinar, 'is_published', False)
        is_published_first_time = form.instance.is_published and not is_previously_published

        if is_published_first_time:
            webinar_team_emails = webinar_emails_for_panelists_co_hosts_and_presenter(webinar)
            webinar_invitees_emails += webinar_team_emails

            webinar.create_team_registrations(User.objects.filter(email__in=webinar_team_emails))
            schedule_webinar_reminders(webinar_team_emails, webinar.to_dict())

        if change and not is_published_first_time:
            if removed_members:
                webinar.remove_team_registrations_and_cancel_reminders(removed_members)

            webinar_update_recipients_emails = []
            send_update_emails = form.cleaned_data.get(SEND_UPDATE_EMAILS_FIELD)
            # Webinar update recipients are to be fetched for both the cases i.e. in case of sending out invitation
            # emails or update emails. Before sending invitation emails, we need to verify that we are not sending an
            # invite to an already registered user, or an already added team member.
            if new_members or webinar_invitees_emails or send_update_emails:
                webinar_update_recipients_emails = webinar.get_webinar_update_recipients_emails()

            if send_update_emails:
                if webinar_update_recipients_emails:
                    send_webinar_emails(
                        MandrillClient.WEBINAR_UPDATED,
                        webinar,
                        webinar_update_recipients_emails
                    )

            if new_members:
                webinar.create_team_registrations(new_members)

                new_member_emails = [user.email for user in new_members]
                schedule_webinar_reminders(new_member_emails, webinar.to_dict())

                webinar_invitees_emails += new_member_emails

            # Remove registered users and team members from invitation emails list (if any are present)
            webinar_invitees_emails = remove_emails_duplicate_in_other_list(
                webinar_invitees_emails, webinar_update_recipients_emails
            )

        if webinar_invitees_emails:
            send_webinar_emails(
                MandrillClient.WEBINAR_CREATED,
                webinar,
                list(set(webinar_invitees_emails)),
            )

    def get_queryset(self, request):
        qs = super(WebinarAdmin, self).get_queryset(request)
        return qs.filter(is_cancelled=False)

    def get_deleted_objects(self, objs, request):
        """
        Overriding this method to prevent delete permissions error on related objects when a webinar is
        deleted (cancelled) from admin site.

        We have overridden the delete method of Webinar model to mark a webinar as cancelled, instead of deleting it.
        Once the webinar is deleted (cancelled) from admin site, the delete view gets a list of related objects by
        calling get_deleted_objects method and checks for admin’s delete permission of those related objects, which
        includes webinar registrations. Since webinar registration’s delete permission is revoked from the admin site,
        the admin delete view show a permission error and does not allow to proceed with the cancellation of the
        webinar. To bypass the permission error, we are overriding this method.

        Note: deleting (cancelling) a webinar does not delete its corresponding webinar registrations, we only need the
        permission so that the webinar can be cancelled successfully
        """
        # pylint: disable=unused-variable
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)

        return deleted_objects, model_count, set(), protected

    def get_readonly_fields(self, request, obj=None):
        """
        Get all the read-only fields for the admin
        """
        readonly_fields = ['created_by', 'modified_by', 'webinar_status', ]

        is_webinar_published = getattr(obj, 'is_published', False)
        if is_webinar_published:
            readonly_fields.append('is_published')

        return readonly_fields


class CancelledWebinarAdmin(WebinarAdminBase):
    """
    Model admin for cancelled webinar
    """

    readonly_fields = ('webinar_status',)

    save_as = False

    def get_queryset(self, request):
        qs = super(CancelledWebinarAdmin, self).get_queryset(request)
        return qs.filter(is_cancelled=True)

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

    list_display = ('webinar', 'user', 'is_registered', 'is_team_member_registration',)
    search_fields = ('webinar__title', 'user__username')
    list_filter = ('webinar',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        """
        To delete a user object successfully, related webinar registration should also be deleted.
        Therefore, the delete permission was given to a specific group.
        """
        return request.user.groups.filter(name=WEBINAR_REGISTRATION_DELETE_PERMISSION_GROUP).exists()


class ReadOnlyUserAdmin(UserAdmin):
    """
    Readonly User admin to allow search when adding users in fields in ADG Admin site
    """

    def has_add_permission(self, request):
        """
        Do not allow admin to add a new User object
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        Do not allow admin to change any User object
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Do not allow admin to delete an existing User object
        """
        return False

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the User model from admin site index
        """
        return {}


admin.site.register(Webinar, WebinarAdmin)
adg_admin_site.register(Webinar, WebinarAdmin)

admin.site.register(CancelledWebinar, CancelledWebinarAdmin)
adg_admin_site.register(CancelledWebinar, CancelledWebinarAdmin)

admin.site.register(WebinarRegistration, WebinarRegistrationAdmin)
adg_admin_site.register(WebinarRegistration, WebinarRegistrationAdmin)

adg_admin_site.register(User, ReadOnlyUserAdmin)
