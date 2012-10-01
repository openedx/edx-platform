import logging
import sys

from django.contrib.auth.models import User, Group

from xmodule.modulestore import Location

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


def add_user_to_course_group(caller, user, location, role):
    # @todo: make sure caller has 'admin' permissions in the course
    if user.is_active and user.is_authenticated:
        groupname = get_course_groupname_for_role(location, role)

        # see if the group exists, or create if new
        (group, created) = Group.objects.get_or_create(name=groupname)
        if created:
            # if newly created, then we have to save it
            group.save()

        user.groups.add(group)
        user.save()
        return True

    return False

def get_user_by_email(email):
    user = None
    # try to look up user
    try:
        user = User.objects.get(email=email)
    except:
        pass

    return user


def remove_user_from_course_group(caller, user, location, role):
    # @todo: make sure caller has 'admin' permissions in the course

    if is_user_in_course_group_role(user, location, role) == True:
        groupname = get_course_groupname_for_role(location, role)

        # make sure the group actually exists
        group = Group.objects.get(name=groupname)
    
        if group is not None:
            user.groups.remove(group)
            user.save()


def is_user_in_course_group_role(user, location, role):
    if user.is_active and user.is_authenticated:
        return user.groups.filter(name=get_course_groupname_for_role(location,role)).count() > 0

    return False

    
