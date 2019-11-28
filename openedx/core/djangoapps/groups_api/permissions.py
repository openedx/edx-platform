"""
Permissions for administering groups of users
"""
from bridgekeeper import perms, rules
from bridgekeeper.rules import Attribute, Is, ManyRelation

from openedx.core.djangoapps.groups_api.models import User, GroupAdminUser

# Is the user active (and their email verified)?
is_user_active = rules.is_authenticated & rules.is_active

# Helper rules used to define the permissions below

# Is the user one of the group administrators?
is_group_administrator = (
    ManyRelation(
        # In newer versions of bridgekeeper, the 1st and 3rd arguments below aren't needed.
        'groupadminuser_set', 'groupadminuser', GroupAdminUser,
        Attribute('user', lambda user: user)
    )
)

# Is the user a member of the group?
is_group_member = (
    ManyRelation(
        'user_set', 'user', User,
        Is(lambda user: user)
    )
)

########################### Permissions ###########################

# Permissions are named according to the standard django permissions naming
# scheme so that they work with bridgekeeper's DRF integration, and so that
# fine-grained permissions can still be assigned manually using standard django.
# https://bridgekeeper.readthedocs.io/en/latest/guides/rest_framework.html#permission-naming

VIEW_GROUP = 'auth.view_group'
CHANGE_GROUP = 'auth.change_group'
ADD_GROUP = 'auth.add_group'
DELETE_GROUP = 'auth.delete_group'
perms[VIEW_GROUP] = is_user_active & (is_group_member | is_group_administrator | rules.is_superuser)
perms[CHANGE_GROUP] = is_user_active & (is_group_administrator | rules.is_superuser)
perms[ADD_GROUP] = is_user_active & (rules.is_staff | rules.is_superuser)
perms[DELETE_GROUP] = perms[CHANGE_GROUP]
