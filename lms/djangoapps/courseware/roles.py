"""
Classes used to model the roles used in the courseware. Each role is responsible for checking membership,
adding users, removing users, and listing members
"""

from abc import ABCMeta, abstractmethod
from functools import partial

from django.contrib.auth.models import User, Group

from xmodule.modulestore import Location


class CourseContextRequired(Exception):
    """
    Raised when a course_context is required to determine permissions
    """
    pass


class AccessRole(object):
    """
    Object representing a role with particular access to a resource
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def has_user(self, user):  # pylint: disable=unused-argument
        """
        Return whether the supplied django user has access to this role.
        """
        return False

    @abstractmethod
    def add_users(self, *users):
        """
        Add the role to the supplied django users.
        """
        pass

    @abstractmethod
    def remove_users(self, *users):
        """
        Remove the role from the supplied django users.
        """
        pass

    @abstractmethod
    def users_with_role(self):
        """
        Return a django QuerySet for all of the users with this role
        """
        return User.objects.none()


class GlobalStaff(AccessRole):
    """
    The global staff role
    """
    def has_user(self, user):
        return user.is_staff

    def add_users(self, *users):
        for user in users:
            user.is_staff = True
            user.save()

    def remove_users(self, *users):
        for user in users:
            user.is_staff = False
            user.save()

    def users_with_role(self):
        raise Exception("This operation is un-indexed, and shouldn't be used")


class GroupBasedRole(AccessRole):
    """
    A role based on membership to any of a set of groups.
    """
    def __init__(self, group_names):
        """
        Create a GroupBasedRole from a list of group names

        The first element of `group_names` will be the preferred group
        to use when adding a user to this Role.

        If a user is a member of any of the groups in the list, then
        they will be consider a member of the Role
        """
        self._group_names = [name.lower() for name in group_names]

    def has_user(self, user):
        """
        Return whether the supplied django user has access to this role.
        """
        # pylint: disable=protected-access
        if not user.is_authenticated():
            return False

        if not hasattr(user, '_groups'):
            user._groups = set(name.lower() for name in user.groups.values_list('name', flat=True))

        return len(user._groups.intersection(self._group_names)) > 0

    def add_users(self, *users):
        """
        Add the supplied django users to this role.
        """
        group, _ = Group.objects.get_or_create(name=self._group_names[0])
        group.user_set.add(*users)
        for user in users:
            if hasattr(user, '_groups'):
                del user._groups

    def remove_users(self, *users):
        """
        Remove the supplied django users from this role.
        """
        group, _ = Group.objects.get_or_create(name=self._group_names[0])
        group.user_set.remove(*users)
        for user in users:
            if hasattr(user, '_groups'):
                del user._groups

    def users_with_role(self):
        """
        Return a django QuerySet for all of the users with this role
        """
        return User.objects.filter(groups__name__in=self._group_names)


class CourseRole(GroupBasedRole):
    """
    A named role in a particular course
    """
    def __init__(self, role, location, course_context=None):
        # pylint: disable=no-member
        loc = Location(location)
        legacy_group_name = '{0}_{1}'.format(role, loc.course)

        if loc.category.lower() == 'course':
            course_id = loc.course_id
        else:
            if course_context is None:
                raise CourseContextRequired()
            course_id = course_context

        group_name = '{0}_{1}'.format(role, course_id)

        super(CourseRole, self).__init__([group_name, legacy_group_name])


class OrgRole(GroupBasedRole):
    """
    A named role in a particular org
    """
    def __init__(self, role, location):
        # pylint: disable=no-member

        location = Location(location)
        super(OrgRole, self).__init__(['{}_{}'.format(role, location.org)])


class CourseStaffRole(CourseRole):
    """A Staff member of a course"""
    def __init__(self, *args, **kwargs):
        super(CourseStaffRole, self).__init__('staff', *args, **kwargs)


class CourseInstructorRole(CourseRole):
    """A course Instructor"""
    def __init__(self, *args, **kwargs):
        super(CourseInstructorRole, self).__init__('instructor', *args, **kwargs)


class CourseBetaTesterRole(CourseRole):
    """A course Beta Tester"""
    def __init__(self, *args, **kwargs):
        super(CourseBetaTesterRole, self).__init__('beta_testers', *args, **kwargs)


class OrgStaffRole(OrgRole):
    """An organization staff member"""
    def __init__(self, *args, **kwargs):
        super(OrgStaffRole, self).__init__('staff', *args, **kwargs)


class OrgInstructorRole(OrgRole):
    """An organization staff member"""
    def __init__(self, *args, **kwargs):
        super(OrgInstructorRole, self).__init__('staff', *args, **kwargs)
