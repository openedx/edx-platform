"""
Role for User Manager Application.
"""
from django.contrib.auth.models import User
from django.db.models import Q

from student.roles import AccessRole
from .models import UserManagerRole


class ManagerRole(AccessRole):
    """
    Maps users to their managers by account or email.
    """

    def __init__(self, managed_user=None):
        """
        Create a ManagerRole accessor for a given ``managed_user``.

        Can be used to determine others user's manager relationship with this
        user, or if no user is supplied, whether they have a manager relationship
        with any user.
        """
        self.managed_user = managed_user

    def _filter_by_managed_user(self, query):
        if self.managed_user is not None:
            return query.filter(user=self.managed_user)
        return query

    def has_user(self, user):
        """
        Return whether the supplied user is a manager for ``managed_user``.
        """
        is_manager = Q(manager_user=user) | Q(unregistered_manager_email=user.email)
        query = self._filter_by_managed_user(
            UserManagerRole.objects.filter(is_manager)
        )
        return query.exists()

    has_manager = has_user

    def add_users(self, *users):
        """
        Add the supplied users as managers for ``managed_user``.
        """
        if self.managed_user is None:
            return
        for manager in users:
            UserManagerRole.objects.create(
                user=self.managed_user,
                manager_user=manager,
            )

    add_manager = add_users

    def add_direct_report(self, *users):
        if self.managed_user is None:
            return
        for user in users:
            UserManagerRole.objects.create(
                user=user,
                manager_user=self.managed_user,
            )

    def remove_users(self, *users):
        """
        Remove the supplied users as managers for ``managed_user``.

        If no ``managed_user`` was supplied, remove them as managers for all users.
        """
        self._filter_by_managed_user(
            UserManagerRole.objects.filter(manager_user__in=users)
        ).delete()

    def users_with_role(self):
        """
        Return all the users that can manage the ``managed_user``.

        If no ``managed_user`` was supplied, return all users that are managers
        for any user.
        """
        manager_ids = self._filter_by_managed_user(
            UserManagerRole.objects.all()
        ).filter(
            manager_user__isnull=False,
        ).values_list('manager_user', flat=True)
        return User.objects.filter(ids__in=manager_ids)

    get_managers = users_with_role
