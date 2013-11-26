"""
Table for storing information about whether or not Studio users have course creation privileges.
"""
from django.db import models
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver, Signal
from django.contrib.auth.models import User

from django.utils import timezone
from django.utils.translation import ugettext as _

# A signal that will be sent when users should be added or removed from the creator group
update_creator_state = Signal(providing_args=["caller", "user", "state"])

# A signal that will be sent when admin should be notified of a pending user request
send_admin_notification = Signal(providing_args=["user"])

# A signal that will be sent when user should be notified of change in course creator privileges
send_user_notification = Signal(providing_args=["user", "state"])


class CourseCreator(models.Model):
    """
    Creates the database table model.
    """
    UNREQUESTED = 'unrequested'
    PENDING = 'pending'
    GRANTED = 'granted'
    DENIED = 'denied'

    # Second value is the "human-readable" version.
    STATES = (
        (UNREQUESTED, _(u'unrequested')),
        (PENDING, _(u'pending')),
        (GRANTED, _(u'granted')),
        (DENIED, _(u'denied')),
    )

    user = models.ForeignKey(User, help_text=_("Studio user"), unique=True)
    state_changed = models.DateTimeField('state last updated', auto_now_add=True,
                                         help_text=_("The date when state was last updated"))
    state = models.CharField(max_length=24, blank=False, choices=STATES, default=UNREQUESTED,
                             help_text=_("Current course creator state"))
    note = models.CharField(max_length=512, blank=True, help_text=_("Optional notes about this user (for example, "
                                                                    "why course creation access was denied)"))

    def __unicode__(self):
        return u"{0} | {1} [{2}]".format(self.user, self.state, self.state_changed)


@receiver(post_init, sender=CourseCreator)
def post_init_callback(sender, **kwargs):
    """
    Extend to store previous state.
    """
    instance = kwargs['instance']
    instance.orig_state = instance.state


@receiver(post_save, sender=CourseCreator)
def post_save_callback(sender, **kwargs):
    """
    Extend to update state_changed time and fire event to update course creator group, if appropriate.
    """
    instance = kwargs['instance']
    # We only wish to modify the state_changed time if the state has been modified. We don't wish to
    # modify it for changes to the notes field.
    if instance.state != instance.orig_state:
        granted_state_change = instance.state == CourseCreator.GRANTED or instance.orig_state == CourseCreator.GRANTED
        # If either old or new state is 'granted', we must manipulate the course creator
        # group maintained by authz. That requires staff permissions (stored admin).
        if granted_state_change:
            assert hasattr(instance, 'admin'), 'Must have stored staff user to change course creator group'
            update_creator_state.send(
                sender=sender,
                caller=instance.admin,
                user=instance.user,
                state=instance.state
            )

        # If user has been denied access, granted access, or previously granted access has been
        # revoked, send a notification message to the user.
        if instance.state == CourseCreator.DENIED or granted_state_change:
            send_user_notification.send(
                sender=sender,
                user=instance.user,
                state=instance.state
            )

        # If the user has gone into the 'pending' state, send a notification to interested admin.
        if instance.state == CourseCreator.PENDING:
            send_admin_notification.send(
                sender=sender,
                user=instance.user
            )

        instance.state_changed = timezone.now()
        instance.orig_state = instance.state
        instance.save()
