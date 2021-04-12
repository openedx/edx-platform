"""
django admin page for the course creators table
"""


import logging
from smtplib import SMTPException

from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib import admin
from django.core.mail import send_mail
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from cms.djangoapps.course_creators.models import (
    CourseCreator,
    send_admin_notification,
    send_user_notification,
    update_creator_state
)
from cms.djangoapps.course_creators.views import update_course_creator_group, update_org_content_creator_role
from common.djangoapps.edxmako.shortcuts import render_to_string

log = logging.getLogger("studio.coursecreatoradmin")


def get_email(obj):
    """ Returns the email address for a user """
    return obj.user.email

get_email.short_description = 'email'

class CourseCreatorForm(forms.ModelForm):
    class Meta:
        model = CourseCreator
        fields = '__all__'

    def clean(self):
        all_orgs = self.cleaned_data.get("all_organizations")
        orgs = self.cleaned_data.get("orgs").exists()
        if orgs and all_orgs:
            raise ValidationError("all_organization should be disabled to use organization restrictions")
        if not orgs and not all_orgs:
            raise ValidationError("Oragnizations should be added if all_organization is disabled")


class CourseCreatorAdmin(admin.ModelAdmin):
    """
    Admin for the course creator table.
    """

    # Fields to display on the overview page.
    list_display = ['username', get_email, 'state', 'state_changed', 'note', 'all_organizations']
    filter_horizontal = ('orgs',)
    readonly_fields = ['username', 'state_changed']
    # Controls the order on the edit form (without this, read-only fields appear at the end).
    fieldsets = (
        (None, {
            'fields': ['username', 'state', 'state_changed', 'note', 'all_organizations', 'orgs']
        }),
    )
    # Fields that filtering support
    list_filter = ['state', 'state_changed']
    # Fields that search supports.
    search_fields = ['user__username', 'user__email', 'state', 'note', 'orgs']
    # Turn off the action bar (we have no bulk actions)
    actions = None
    form=CourseCreatorForm

    def username(self, inst):
        """
        Returns the username for a given user.

        Implemented to make sorting by username instead of by user object.
        """
        return inst.user.username

    username.admin_order_field = 'user__username'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def save_model(self, request, obj, form, change):
        # Store who is making the request.
        obj.admin = request.user
        obj.save()


admin.site.register(CourseCreator, CourseCreatorAdmin)


@receiver(update_creator_state, sender=CourseCreator)
def update_creator_group_callback(sender, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
    """
    Callback for when the model's creator status has changed.
    """
    user = kwargs['user']
    updated_state = kwargs['state']
    all_orgs = kwargs['all_organizations']
    if all_orgs:
        update_course_creator_group(kwargs['caller'], user, updated_state == CourseCreator.GRANTED)


@receiver(send_user_notification, sender=CourseCreator)
def send_user_notification_callback(sender, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
    """
    Callback for notifying user about course creator status change.
    """
    user = kwargs['user']
    updated_state = kwargs['state']

    studio_request_email = settings.FEATURES.get('STUDIO_REQUEST_EMAIL', '')
    context = {'studio_request_email': studio_request_email}

    subject = render_to_string('emails/course_creator_subject.txt', context)
    subject = ''.join(subject.splitlines())
    if updated_state == CourseCreator.GRANTED:
        message_template = 'emails/course_creator_granted.txt'
    elif updated_state == CourseCreator.DENIED:
        message_template = 'emails/course_creator_denied.txt'
    else:
        # changed to unrequested or pending
        message_template = 'emails/course_creator_revoked.txt'
    message = render_to_string(message_template, context)

    try:
        user.email_user(subject, message, studio_request_email)
    except:  # lint-amnesty, pylint: disable=bare-except
        log.warning("Unable to send course creator status e-mail to %s", user.email)


@receiver(send_admin_notification, sender=CourseCreator)
def send_admin_notification_callback(sender, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
    """
    Callback for notifying admin of a user in the 'pending' state.
    """
    user = kwargs['user']

    studio_request_email = settings.FEATURES.get('STUDIO_REQUEST_EMAIL', '')
    context = {'user_name': user.username, 'user_email': user.email}

    subject = render_to_string('emails/course_creator_admin_subject.txt', context)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/course_creator_admin_user_pending.txt', context)

    try:
        send_mail(
            subject,
            message,
            studio_request_email,
            [studio_request_email],
            fail_silently=False
        )
    except SMTPException:
        log.warning("Failure sending 'pending state' e-mail for %s to %s", user.email, studio_request_email)


@receiver(m2m_changed, sender=CourseCreator.orgs.through)
def post_all_organizations_callback(sender, **kwargs):
    """
    Callback for addition and removal for orgs field.
    """
    instance = kwargs["instance"]
    action = kwargs["action"]
    orgs = list(instance.orgs.all().values_list('short_name', flat=True))
    if action in ["post_add", "post_remove"]:
        update_org_content_creator_role(instance.admin, instance.user, orgs)
