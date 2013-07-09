"""
Table for storing information about whether or not Studio users have course creation privileges.
"""
from django.db import models
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver, Signal
from django.contrib.auth.models import User

from django.utils import timezone

# A signal that will be sent when users should be added or removed from the creator group
update_creator_state = Signal(providing_args=["caller", "user", "add"])

class CourseCreator(models.Model):
    """
    Creates the database table model.
    """
    STATES = (
        (u'u', u'unrequested'),
        (u'p', u'pending'),
        (u'g', u'granted'),
        (u'd', u'denied'),
    )

    user = models.ForeignKey(User, help_text="Studio user", unique=True)
    state_changed = models.DateTimeField('state last updated', auto_now_add=True,
                                         help_text='The date when state was last updated')
    state = models.CharField(max_length=1, blank=False, choices=STATES, default='u',
                             help_text='Current course creator state')
    note = models.CharField(max_length=512, blank=True, help_text='Optional notes about this user (for example, '
                                                                  'why course creation access was denied)')

    def __unicode__(self):
        s = "%str | %str [%str] | %str" % (self.user, self.state, self.state_changed, self.note)
        return s


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
    Extend to update state_changed time and modify the course creator group in authz.py.
    """
    instance = kwargs['instance']
    # We only wish to modify the state_changed time if the state has been modified. We don't wish to
    # modify it for changes to the notes field.
    if instance.state != instance.orig_state:
        update_creator_state.send(
            sender=sender,
            caller=instance.admin,
            user=instance.user,
            add=instance.state == 'g'
        )
        instance.state_changed = timezone.now()
        instance.orig_state = instance.state
        instance.save()
