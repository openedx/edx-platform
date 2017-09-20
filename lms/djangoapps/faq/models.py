from django.db import models
from student.models import User
from django.utils import timezone


class Faq(models.Model):
    title = models.CharField(max_length=128, default="FAQ")
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(User, related_name='faq_user')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return '{} | {}'.format(self.title, self.is_active)
