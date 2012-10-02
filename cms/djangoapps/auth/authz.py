import logging
import sys

from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied

from xmodule.modulestore import Location

# define a couple of simple roles, we just need ADMIN and EDITOR now for our purposes
ADMIN_ROLE_NAME = 'admin'
EDITOR_ROLE_NAME = 'editor'

# we're just making a Django group for each location/role combo
# to do this we're just creating a Group name which is a formatted string
# of those two variables
def get_course_groupname_for_role(location, role):
    loc = Location(location)
    groupname = loc.course_id  + ':' + role
    return groupname

def get_users_in_course_group_by_role(location, role):
    groupname = get_course_groupname_for_role(location, role)
    group = Group.objects.get(name=groupname)
    return group.user_set.all()


'''
Create all permission groups for a new course and subscribe the caller into those roles
'''
def create_all_course_groups(creator, location):
    create_new_course_group(creator, location, ADMIN_GROUP_NAME)
    create_new_course_group(creator, location, EDITOR_GROUP_NAME)


def create_new_course_group(creator, location, role):
    groupname = get_course_groupname_for_role(location, role)
    (group, created) =Group.get_or_create(name=groupname)
    if created:
        group.save()

    creator.groups.add(group)
    creator.save()

    return


def add_user_to_course_group(caller, user, location, role):
    # only admins can add/remove other users
    if not is_user_in_course_group_role(caller, location, ADMIN_ROLE_NAME):
        raise PermissionDenied

    if user.is_active and user.is_authenticated:
        groupname = get_course_groupname_for_role(location, role)

        group = Group.objects.get(name=groupname)
        user.groups.add(group)
        user.save()
        return True

    return False


def get_user_by_email(email):
    user = None
    # try to look up user, return None if not found
    try:
        user = User.objects.get(email=email)
    except:
        pass

    return user


def remove_user_from_course_group(caller, user, location, role):
    # only admins can add/remove other users
    if not is_user_in_course_group_role(caller, location, ADMIN_ROLE_NAME):
        raise PermissionDenied

    # see if the user is actually in that role, if not then we don't have to do anything
    if is_user_in_course_group_role(user, location, role) == True:
        groupname = get_course_groupname_for_role(location, role)

        group = Group.objects.get(name=groupname)
        user.groups.remove(group)
        user.save()


def is_user_in_course_group_role(user, location, role):
    if user.is_active and user.is_authenticated:
        # all "is_staff" flagged accounts belong to all groups
        return user.is_staff or user.groups.filter(name=get_course_groupname_for_role(location,role)).count() > 0

    return False

    
