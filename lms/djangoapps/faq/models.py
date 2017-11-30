from django.db import models
from student.models import User
from django.utils import timezone


class Faq(models.Model):
    """
    Model to save the data of FAQ page dynamically
    """
    title = models.CharField(max_length=128, default="FAQ")
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(User, related_name='faq_user')
    updated_by = models.ForeignKey(User, null=True, blank=True, related_name='faq_updated_by')
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return '{} | {}'.format(self.title, self.is_active)
