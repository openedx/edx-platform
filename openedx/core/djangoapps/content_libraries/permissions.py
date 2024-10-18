"""
Permissions for Content Libraries (v2, Learning-Core-based)
"""
from bridgekeeper import perms, rules
from bridgekeeper.rules import Attribute, ManyRelation, Relation, blanket_rule, in_current_groups
from django.conf import settings

from openedx.core.djangoapps.content_libraries.models import ContentLibraryPermission

# Is the user active (and their email verified)?
is_user_active = rules.is_authenticated & rules.is_active
# Is the user global staff?
is_global_staff = is_user_active & rules.is_staff

# Helper rules used to define the permissions below

# Does the user have at least read permission for the specified library?
has_explicit_read_permission_for_library = (
    ManyRelation(
        'permission_grants',
        (Attribute('user', lambda user: user) | Relation('group', in_current_groups))
    )
    # We don't check 'access_level' here because all access levels grant read permission
)
# Does the user have at least author permission for the specified library?
has_explicit_author_permission_for_library = (
    ManyRelation(
        'permission_grants',
        (Attribute('user', lambda user: user) | Relation('group', in_current_groups)) & (
            Attribute('access_level', ContentLibraryPermission.AUTHOR_LEVEL) |
            Attribute('access_level', ContentLibraryPermission.ADMIN_LEVEL)
        )
    )
)
# Does the user have admin permission for the specified library?
has_explicit_admin_permission_for_library = (
    ManyRelation(
        'permission_grants',
        (Attribute('user', lambda user: user) | Relation('group', in_current_groups)) &
        Attribute('access_level', ContentLibraryPermission.ADMIN_LEVEL)
    )
)


# Are we in Studio? (Is there a better or more contextual way to define this, e.g. get from learning context?)
@blanket_rule
def is_studio_request(_):
    return settings.SERVICE_VARIANT == "cms"


########################### Permissions ###########################

# Is the user allowed to view XBlocks from the specified content library
# directly in the LMS, and interact with them?
# Note there is no is_authenticated/is_active check for this one - we allow
# anonymous users to learn if the library allows public learning.
CAN_LEARN_FROM_THIS_CONTENT_LIBRARY = 'content_libraries.learn_from_library'
perms[CAN_LEARN_FROM_THIS_CONTENT_LIBRARY] = (
    # Global staff can learn from any library:
    is_global_staff |
    # Regular and even anonymous users can learn if the library allows public learning:
    Attribute('allow_public_learning', True) |
    # Users/groups who are explicitly granted permission can learn from the library:
    (is_user_active & has_explicit_read_permission_for_library) |
    # Or, in Studio (but not the LMS) any users can access libraries with "public read" permissions:
    (is_studio_request & is_user_active & Attribute('allow_public_read', True))
)

# Is the user allowed to create content libraries?
CAN_CREATE_CONTENT_LIBRARY = 'content_libraries.create_library'
perms[CAN_CREATE_CONTENT_LIBRARY] = is_user_active

# Is the user allowed to view the specified content library in Studio,
# including to view the raw OLX and asset files?
CAN_VIEW_THIS_CONTENT_LIBRARY = 'content_libraries.view_library'
perms[CAN_VIEW_THIS_CONTENT_LIBRARY] = is_user_active & (
    # Global staff can access any library
    is_global_staff |
    # Some libraries allow anyone to view them in Studio:
    Attribute('allow_public_read', True) |
    # Otherwise the user must be part of the library's team
    has_explicit_read_permission_for_library
)

# Is the user allowed to edit the specified content library?
CAN_EDIT_THIS_CONTENT_LIBRARY = 'content_libraries.edit_library'
perms[CAN_EDIT_THIS_CONTENT_LIBRARY] = is_user_active & (
    is_global_staff | has_explicit_author_permission_for_library
)

# Is the user allowed to view the users/permissions of the specified content library?
CAN_VIEW_THIS_CONTENT_LIBRARY_TEAM = 'content_libraries.view_library_team'
perms[CAN_VIEW_THIS_CONTENT_LIBRARY_TEAM] = perms[CAN_EDIT_THIS_CONTENT_LIBRARY]

# Is the user allowed to edit the users/permissions of the specified content library?
CAN_EDIT_THIS_CONTENT_LIBRARY_TEAM = 'content_libraries.edit_library_team'
perms[CAN_EDIT_THIS_CONTENT_LIBRARY_TEAM] = is_user_active & (
    is_global_staff | has_explicit_admin_permission_for_library
)

# Is the user allowed to delete the specified content library?
CAN_DELETE_THIS_CONTENT_LIBRARY = 'content_libraries.delete_library'
perms[CAN_DELETE_THIS_CONTENT_LIBRARY] = is_user_active & (
    is_global_staff | has_explicit_admin_permission_for_library
)
