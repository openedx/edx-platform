from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class UserManagerRole(models.Model):
    """
    Creates a manager-managee link between users.


    .. note::
        In case the manager doesn't have an account registered in the system,
        their email will be linked instead, and auto-upgraded to a foreign key
        when they register an account.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='+',
    )
    manager_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='+',
    )
    # This will get upgraded to a foreign key to the manager's user account
    # when they register.
    unregistered_manager_email = models.EmailField(
        help_text="The email address for a manager if they haven't currently "
                  "registered for an account."
    )

    class Meta(object):
        app_label = 'user_manager'
        ordering = ['manager_user']
        unique_together = (
            ('user', 'manager_user'),
            ('user', 'unregistered_manager_email'),
        )

    @property
    def manager_email(self):
        if self.manager_user:
            return self.manager_user.email
        else:
            return self.unregistered_manager_email

    def clean(self):
        if (
                self.user == self.manager_user or
                self.user.email == self.unregistered_manager_email
        ):
            raise ValidationError('User and manager cannot be the same')
