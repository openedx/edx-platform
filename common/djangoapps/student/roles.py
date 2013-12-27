"""
Classes used to model the roles used in the courseware. Each role is responsible for checking membership,
adding users, removing users, and listing members
"""

from abc import ABCMeta, abstractmethod

from django.contrib.auth.models import User, Group

from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.locator import CourseLocator, Locator


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
    def __init__(self, role, location, course_context=None):
        """
        Location may be either a Location, a string, dict, or tuple which Location will accept
        in its constructor, or a CourseLocator. Handle all these giving some preference to
        the preferred naming.
        """
        # TODO: figure out how to make the group name generation lazy so it doesn't force the
        # loc mapping?
        self.location = Locator.to_locator_or_location(location)
        self.role = role
        # direct copy from auth.authz.get_all_course_role_groupnames will refactor to one impl asap
        groupnames = []

        # pylint: disable=no-member
        if isinstance(self.location, Location):
            try:
                groupnames.append('{0}_{1}'.format(role, self.location.course_id))
                course_context = self.location.course_id  # course_id is valid for translation
            except InvalidLocationError:  # will occur on old locations where location is not of category course
                if course_context is None:
                    raise CourseContextRequired()
                else:
                    groupnames.append('{0}_{1}'.format(role, course_context))
            try:
                locator = loc_mapper().translate_location(course_context, self.location, False, False)
                groupnames.append('{0}_{1}'.format(role, locator.package_id))
            except (InvalidLocationError, ItemNotFoundError):
                # if it's never been mapped, the auth won't be via the Locator syntax
                pass
            # least preferred legacy role_course format
            groupnames.append('{0}_{1}'.format(role, self.location.course))
        elif isinstance(self.location, CourseLocator):
            groupnames.append('{0}_{1}'.format(role, self.location.package_id))
            # handle old Location syntax
            old_location = loc_mapper().translate_locator_to_location(self.location, get_course=True)
            if old_location:
                # the slashified version of the course_id (myu/mycourse/myrun)
                groupnames.append('{0}_{1}'.format(role, old_location.course_id))
                # add the least desirable but sometimes occurring format.
                groupnames.append('{0}_{1}'.format(role, old_location.course))

        super(CourseRole, self).__init__(groupnames)


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
        super(CourseCreatorRole, self).__init__(self.ROLE, *args, **kwargs)
