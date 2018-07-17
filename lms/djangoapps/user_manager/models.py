from django.contrib.auth.models import User
from django.db import models


class UserManagerRole(models.Model):
    """
    Creates a manager-managee link between users.


    .. note::
        In case the manager doesn't have an account registered in the system,
        their email will be linked instead, and auto-upgraded to a foreign key
        when they register an account.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    manager_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    # This will get upgraded to a foreign key to the manager's user account
    # when they register.
    unregistered_manager_email = models.EmailField(
        help_text="The email address for a manager if they haven't currently "
                  "registered for an account."
    )

    class Meta:
        unique_together = (
            ('user', 'manager_user'),
            ('user', 'unregistered_manager_email'),
        )

