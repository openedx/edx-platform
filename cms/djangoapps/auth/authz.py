"""
Studio authorization functions primarily for course creators, instructors, and staff
"""
#=======================================================================================================================
#
# This code is somewhat duplicative of access.py in the LMS. We will unify the code as a separate story
# but this implementation should be data compatible with the LMS implementation
#
#=======================================================================================================================
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from django.conf import settings

from xmodule.modulestore import Location
from xmodule.modulestore.locator import CourseLocator, Locator
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError
import itertools


# define a couple of simple roles, we just need ADMIN and EDITOR now for our purposes
INSTRUCTOR_ROLE_NAME = 'instructor'
STAFF_ROLE_NAME = 'staff'

# This is the group of people who have permission to create new courses on edge or edx.
COURSE_CREATOR_GROUP_NAME = "course_creator_group"

# we're just making a Django group for each location/role combo
# to do this we're just creating a Group name which is a formatted string
# of those two variables


def get_all_course_role_groupnames(location, role, use_filter=True):
    '''
    Get all of the possible groupnames for this role location pair. If use_filter==True,
    only return the ones defined in the groups collection.
    '''
    location = Locator.to_locator_or_location(location)

    groupnames = []
    if isinstance(location, Location):
        try:
            groupnames.append(u'{0}_{1}'.format(role, location.course_id))
        except InvalidLocationError:  # will occur on old locations where location is not of category course
            pass
        try:
            locator = loc_mapper().translate_location(location.course_id, location, False, False)
            groupnames.append(u'{0}_{1}'.format(role, locator.package_id))
        except (InvalidLocationError, ItemNotFoundError):
            pass
        # least preferred role_course format for legacy reasons
        groupnames.append(u'{0}_{1}'.format(role, location.course))
    elif isinstance(location, CourseLocator):
        groupnames.append(u'{0}_{1}'.format(role, location.package_id))
        old_location = loc_mapper().translate_locator_to_location(location, get_course=True)
        if old_location:
            # the slashified version of the course_id (myu/mycourse/myrun)
            groupnames.append(u'{0}_{1}'.format(role, old_location.course_id))
            # add the least desirable but sometimes occurring format.
            groupnames.append(u'{0}_{1}'.format(role, old_location.course))
    # filter to the ones which exist
    default = groupnames[0]
    if use_filter:
        groupnames = [group.name for group in Group.objects.filter(name__in=groupnames)]
    return groupnames, default


def get_course_groupname_for_role(location, role):
    '''
    Get the preferred used groupname for this role, location combo.
    Preference order: 
    * role_course_id (e.g., staff_myu.mycourse.myrun)
    * role_old_course_id (e.g., staff_myu/mycourse/myrun)
    * role_old_course (e.g., staff_mycourse)
    '''
    groupnames, default = get_all_course_role_groupnames(location, role)
    return groupnames[0] if groupnames else default


def get_course_role_users(course_locator, role):
    '''
    Get all of the users with the given role in the given course.
    '''
    groupnames, _ = get_all_course_role_groupnames(course_locator, role)
    groups = [Group.objects.get(name=groupname) for groupname in groupnames]
    return list(itertools.chain.from_iterable(group.user_set.all() for group in groups))


def create_all_course_groups(creator, location):
    """
    Create all permission groups for a new course and subscribe the caller into those roles
    """
    create_new_course_group(creator, location, INSTRUCTOR_ROLE_NAME)
    create_new_course_group(creator, location, STAFF_ROLE_NAME)


def create_new_course_group(creator, location, role):
    '''
    Create the new course group always using the preferred name even if another form already exists.
    '''
    groupnames, __ = get_all_course_role_groupnames(location, role, use_filter=False)
    group, __ = Group.objects.get_or_create(name=groupnames[0])
    creator.groups.add(group)
    creator.save()

    return


def _delete_course_group(location):
    """
    This is to be called only by either a command line code path or through a app which has already
    asserted permissions
    """
    # remove all memberships
    for role in [INSTRUCTOR_ROLE_NAME, STAFF_ROLE_NAME]:
        groupnames, _ = get_all_course_role_groupnames(location, role)
        for groupname in groupnames:
            group = Group.objects.get(name=groupname)
            for user in group.user_set.all():
                user.groups.remove(group)
                user.save()


def _copy_course_group(source, dest):
    """
    This is to be called only by either a command line code path or through an app which has already
    asserted permissions to do this action
    """
    for role in [INSTRUCTOR_ROLE_NAME, STAFF_ROLE_NAME]:
        groupnames, _ = get_all_course_role_groupnames(source, role)
        for groupname in groupnames:
            group = Group.objects.get(name=groupname)
            new_group, _ = Group.objects.get_or_create(name=get_course_groupname_for_role(dest, INSTRUCTOR_ROLE_NAME))
            for user in group.user_set.all():
                user.groups.add(new_group)
                user.save()


def add_user_to_course_group(caller, user, location, role):
    """
    If caller is authorized, add the given user to the given course's role
    """
    # only admins can add/remove other users
    if not is_user_in_course_group_role(caller, location, INSTRUCTOR_ROLE_NAME):
        raise PermissionDenied

    group, _ = Group.objects.get_or_create(name=get_course_groupname_for_role(location, role))
    return _add_user_to_group(user, group)


def add_user_to_creator_group(caller, user):
    """
    Adds the user to the group of course creators.

    The caller must have staff access to perform this operation.

    Note that on the edX site, we currently limit course creators to edX staff, and this
    method is a no-op in that environment.
    """
    if not caller.is_active or not caller.is_authenticated or not caller.is_staff:
        raise PermissionDenied

    (group, _) = Group.objects.get_or_create(name=COURSE_CREATOR_GROUP_NAME)
    return _add_user_to_group(user, group)


def _add_user_to_group(user, group):
    """
    This is to be called only by either a command line code path or through an app which has already
    asserted permissions to do this action
    """
    if user.is_active and user.is_authenticated:
        user.groups.add(group)
        user.save()
        return True

    return False


def get_user_by_email(email):
    """
    Get the user whose email is the arg. Return None if no such user exists.
    """
    user = None
    # try to look up user, return None if not found
    try:
        user = User.objects.get(email=email)
    except:
        pass

    return user


def remove_user_from_course_group(caller, user, location, role):
    """
    If caller is authorized, remove the given course x role authorization for user
    """
    # only admins can add/remove other users
    if not is_user_in_course_group_role(caller, location, INSTRUCTOR_ROLE_NAME):
        raise PermissionDenied

    # see if the user is actually in that role, if not then we don't have to do anything
    groupnames, _ = get_all_course_role_groupnames(location, role)
    user.groups.remove(*user.groups.filter(name__in=groupnames))
    user.save()


def remove_user_from_creator_group(caller, user):
    """
    Removes user from the course creator group.

    The caller must have staff access to perform this operation.
    """
    if not caller.is_active or not caller.is_authenticated or not caller.is_staff:
        raise PermissionDenied

    _remove_user_from_group(user, COURSE_CREATOR_GROUP_NAME)


def _remove_user_from_group(user, group_name):
    """
    This is to be called only by either a command line code path or through an app which has already
    asserted permissions to do this action
    """
    group = Group.objects.get(name=group_name)
    user.groups.remove(group)
    user.save()


def is_user_in_course_group_role(user, location, role, check_staff=True):
    """
    Check whether the given user has the given role in this course. If check_staff
    then give permission if the user is staff without doing a course-role query.
    """
    if user.is_active and user.is_authenticated:
        # all "is_staff" flagged accounts belong to all groups
        if check_staff and user.is_staff:
            return True
        groupnames, _ = get_all_course_role_groupnames(location, role)
        return user.groups.filter(name__in=groupnames).exists()

    return False


def is_user_in_creator_group(user):
    """
    Returns true if the user has permissions to create a course.

    Will always return True if user.is_staff is True.

    Note that on the edX site, we currently limit course creators to edX staff. On
    other sites, this method checks that the user is in the course creator group.
    """
    if user.is_staff:
        return True

    # On edx, we only allow edX staff to create courses. This may be relaxed in the future.
    if settings.FEATURES.get('DISABLE_COURSE_CREATION', False):
        return False

    # Feature flag for using the creator group setting. Will be removed once the feature is complete.
    if settings.FEATURES.get('ENABLE_CREATOR_GROUP', False):
        return user.groups.filter(name=COURSE_CREATOR_GROUP_NAME).exists()

    return True


def get_users_with_instructor_role():
    """
    Returns all users with the role 'instructor'
    """
    return _get_users_with_role(INSTRUCTOR_ROLE_NAME)


def get_users_with_staff_role():
    """
    Returns all users with the role 'staff'
    """
    return _get_users_with_role(STAFF_ROLE_NAME)


def _get_users_with_role(role):
    """
    Returns all users with the specified role.
    """
    users = set()
    for group in Group.objects.all():
        if group.name.startswith(role + "_"):
            for user in group.user_set.all():
                users.add(user)
    return users
