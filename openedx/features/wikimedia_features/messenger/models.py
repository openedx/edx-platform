"""
Messenger Models
"""
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User

APP_LABEL = 'messenger'


class MessageHistoryManager(models.Manager):
    def history(self, user1, user2):
        return self.get_queryset().filter(
            (Q(sender=user1) & Q(receiver=user2)) |
            (Q(sender=user2) & Q(receiver=user1))
        ).order_by('-created')


class Message(models.Model):
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receiver')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender')
    chat = MessageHistoryManager()
    objects = models.Manager()

    def __str__(self):
        return "from: {}, to: {}, message: {}".format(
            self.sender.username,
            self.receiver.username,
            self.message[:20]
        )

    def full_clean(self):
        super().full_clean()
        if self.sender == self.receiver:
            raise ValidationError('Sender can not send message to himself.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(Message, self).save(*args, **kwargs)

    class Meta:
        app_label = APP_LABEL
        indexes = [
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['created']),
        ]


class UserInboxManager(models.Manager):
    def find_all(self, user):
        return super().get_queryset().filter(
            Q(last_message__sender=user) |
            Q(last_message__receiver=user)
        ).order_by('-last_message__created')


class Inbox(models.Model):
    unread_count = models.IntegerField(default=0)
    last_message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='last_message')
    objects = models.Manager()
    user_inbox = UserInboxManager()

    class Meta:
        app_label = APP_LABEL
