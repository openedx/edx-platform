"""
Table for storing information about whether or not Studio users have course creation privileges.
"""
from django.db import models


class CourseCreators(models.Model):
    """
    Creates the database table model.
    """
    STATES = (
        (u'u', u'unrequested'),
        (u'p', u'pending'),
        (u'g', u'granted'),
        (u'd', u'denied'),
        )

    username = models.CharField(max_length=64, blank=False, help_text="Studio username", primary_key=True, unique=True)
    state_changed = models.DateTimeField('state last updated', auto_now_add=True,
                                         help_text='The date when state was last updated')
    state = models.CharField(max_length=1, blank=False, choices=STATES, default='u',
                             help_text='Current course creator state')
    note = models.CharField(max_length=512, blank=True, help_text='Optional notes about this user (for example, '
                                                                  'why course creation access was denied)')

    def __unicode__(self):
        s = "%s | %s [%s] | %s" % (self.username, self.state, self.state_changed, self.note)
        return s

