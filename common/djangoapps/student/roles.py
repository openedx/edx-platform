"""
Classes used to model the roles used in the courseware. Each role is responsible for checking membership,
adding users, removing users, and listing members
"""

from abc import ABCMeta, abstractmethod

from django.contrib.auth.models import User, Group


class CourseIdRequired(Exception):
    """
    Raised when a course_id is required to determine permissions
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
            if (user.is_authenticated and user.is_active):
                user.is_staff = True
                user.save()

    def remove_users(self, *users):
        for user in users:
            # don't check is_authenticated nor is_active on purpose
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
        if not (user.is_authenticated and user.is_active):
            return False

        # pylint: disable=protected-access
        if not hasattr(user, '_groups'):
            user._groups = set(name.lower() for name in user.groups.values_list('name', flat=True))

        return len(user._groups.intersection(self._group_names)) > 0

    def add_users(self, *users):
        """
        Add the supplied django users to this role.
        """
        # silently ignores anonymous and inactive users so that any that are
        # legit get updated.
        users = [user for user in users if user.is_authenticated and user.is_active]
        group, _ = Group.objects.get_or_create(name=self._group_names[0])
        group.user_set.add(*users)
        # remove cache
        for user in users:
            if hasattr(user, '_groups'):
                del user._groups

    def remove_users(self, *users):
        """
        Remove the supplied django users from this role.
        """
        groups = Group.objects.filter(name__in=self._group_names)
        for group in groups:
            group.user_set.remove(*users)
        # remove cache
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
    def __init__(self, role, course_id):
        """
        Location may be either a Location, a string, dict, or tuple which Location will accept
        in its constructor, or a CourseLocator. Handle all these giving some preference to
        the preferred naming.
        """
        self.course_id = course_id
        self.role = role
        # direct copy from auth.authz.get_all_course_role_groupnames will refactor to one impl asap
        groupnames = []

        groupnames.append(u'{0}_{1}'.format(role, self.course_id))
        super(CourseRole, self).__init__(groupnames)

    @classmethod
    def course_group_already_exists(self, course_key):
        # Case insensitive search -- looking for a Group that ends with the course's id
        return Group.objects.filter(name__iendswith=course_key)


class OrgRole(GroupBasedRole):
    """
    A named role in a particular org
    """
    def __init__(self, role, course_id):
        super(OrgRole, self).__init__([u'{}_{}'.format(role, course_id.org)])


class CourseStaffRole(CourseRole):
    """A Staff member of a course"""
    ROLE = 'staff'

    def __init__(self, *args, **kwargs):
        super(CourseStaffRole, self).__init__(self.ROLE, *args, **kwargs)


class CourseInstructorRole(CourseRole):
    """A course Instructor"""
    ROLE = 'instructor'

    def __init__(self, *args, **kwargs):
        super(CourseInstructorRole, self).__init__(self.ROLE, *args, **kwargs)


class CourseBetaTesterRole(CourseRole):
    """A course Beta Tester"""
    ROLE = 'beta_testers'

    def __init__(self, *args, **kwargs):
        super(CourseBetaTesterRole, self).__init__(self.ROLE, *args, **kwargs)


class OrgStaffRole(OrgRole):
    """An organization staff member"""
    def __init__(self, *args, **kwargs):
        super(OrgStaffRole, self).__init__('staff', *args, **kwargs)


class OrgInstructorRole(OrgRole):
    """An organization instructor"""
    def __init__(self, *args, **kwargs):
        super(OrgInstructorRole, self).__init__('instructor', *args, **kwargs)


class CourseCreatorRole(GroupBasedRole):
    """
    This is the group of people who have permission to create new courses (we may want to eventually
    make this an org based role).
    """
    ROLE = "course_creator_group"

    def __init__(self, *args, **kwargs):
        super(CourseCreatorRole, self).__init__([self.ROLE], *args, **kwargs)
