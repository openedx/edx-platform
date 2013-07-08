"""
Table for storing information about whether or not Studio users have course creation privileges.
"""
from django.db import models
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver
from auth.authz import add_user_to_creator_group, remove_user_from_creator_group, get_user_by_email

from django.utils import timezone


class CourseCreator(models.Model):
    """
    Creates the database table model.
    """
    STATES = ((u'u', u'unrequested'),
              (u'p', u'pending'),
              (u'g', u'granted'),
              (u'd', u'denied'),
             )

    username = models.CharField(max_length=64, blank=False, help_text="Studio username", primary_key=True, unique=True)
    email = models.CharField(max_length=128, blank=False, help_text="Registered e-mail address")
    state_changed = models.DateTimeField('state last updated', auto_now_add=True,
                                         help_text='The date when state was last updated')
    state = models.CharField(max_length=1, blank=False, choices=STATES, default='u',
                             help_text='Current course creator state')
    note = models.CharField(max_length=512, blank=True, help_text='Optional notes about this user (for example, '
                                                                  'why course creation access was denied)')

    def __unicode__(self):
        s = "%str %str | %str [%str] | %str" % (self.username, self.email, self.state, self.state_changed, self.note)
        return s


@receiver(post_init, sender=CourseCreator)
def post_init_callback(sender, **kwargs):
    """
    Extend to remove deleted users and store previous state.
    """
    instance = kwargs['instance']
    user = get_user_by_email(instance.email)
    if user is None:
        # User has been removed, delete from this table.
        instance.delete()
    else:
        instance.orig_state = instance.state


@receiver(post_save, sender=CourseCreator)
def post_save_callback(sender, **kwargs):
    """
    Extend to remove deleted users, update state_changed time,
    and modify the course creator group in authz.py.
    """
    instance = kwargs['instance']
    # We only wish to modify the state_changed time if the state has been modified. We don't wish to
    # modify it for changes to the notes field.
    if instance.state != instance.orig_state:
        user = get_user_by_email(instance.email)
        if user is None:
            # User has been removed, delete from this table.
            instance.delete()
        else:
            instance.state_changed = timezone.now()
            if instance.state == 'g':
                # We have granted access, add to course group
                add_user_to_creator_group(instance.admin, user)
            else:
                remove_user_from_creator_group(instance.admin, user)

            instance.orig_state = instance.state
            instance.save()
