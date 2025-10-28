"""
Permissions for Content Libraries (v2, Learning-Core-based)
"""
from bridgekeeper import perms, rules
from bridgekeeper.rules import Attribute, ManyRelation, Relation, blanket_rule, in_current_groups, Rule
from django.conf import settings
from django.db.models import Q

from openedx_authz.api.users import is_user_allowed, get_scopes_for_user_and_permission

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


@blanket_rule
def is_course_creator(user):
    from cms.djangoapps.course_creators.views import get_course_creator_status

    return get_course_creator_status(user) == 'granted'


class HasPermissionInContentLibraryScope(Rule):
    """Bridgekeeper rule that checks permissions via Casbin's policy engine.

    This rule integrates Casbin's role-based authorization with Bridgekeeper's
    declarative permission system. It checks if a user has been granted a specific
    permission (action) through their role assignments in Casbin.

    The rule works by:
    1. Querying Casbin grouping policies to find the user's role assignments
    2. Querying Casbin permission policies to find which roles grant the action
    3. Matching role assignments with scopes to determine where the user has permission

    This enables both individual object permission checks and efficient QuerySet
    filtering - a key feature that allows database-level filtering instead of
    checking each object individually.

    Attributes:
        action_external_key (str): The action/permission to check (e.g., 'view', 'edit').
            This should be the external key WITHOUT the namespace prefix.
            For example, use 'view' not 'act^view'.

        scope_field (str): The Django model field/property that contains the scope identifier.
            This tells the rule WHERE to find the scope value in your model.
            Defaults to 'id'.

            **IMPORTANT**: This can be a model property (like `library_key`) or a field.
            For ContentLibrary, use 'library_key' which is a @property that returns
            the LibraryLocatorV2 string representation.

            The scope_field serves two purposes:
            - **For QuerySet filtering**: Builds SQL like `WHERE scope_field IN (...)`
            - **For object checks**: Extracts the scope from `instance.scope_field`

            Supports Django ORM field lookups for nested fields:
            - 'library_key' - a @property on the model (ContentLibrary case)
            - 'id' - direct field on the model
            - 'library__id' - field on a related model
            - 'course__org__key' - multi-level relationship

    Examples:
        Basic usage with default scope_field:
            >>> from bridgekeeper import perms
            >>> from openedx_authz.permissions import HasPermissionInScope
            >>>
            >>> # Assumes the model's 'id' field contains the scope
            >>> can_view = HasPermissionInScope('view')
            >>> perms['libraries.view'] = can_view

        Specifying a custom scope_field:
            >>> # When scope is in a field named 'library_id'
            >>> can_view = HasPermissionInScope('view', scope_field='library_id')
            >>>
            >>> # When scope is in a related model
            >>> can_manage = HasPermissionInScope('manage', scope_field='library__key')

        Compound permissions with boolean operators:
            >>> from bridgekeeper.rules import Attribute
            >>>
            >>> is_active = Attribute('is_active', True)
            >>> is_staff = Attribute('is_staff', True)
            >>> can_view = HasPermissionInScope('view', scope_field='library_id')
            >>>
            >>> # User must be active AND (staff OR have explicit permission)
            >>> perms['libraries.view'] = is_active & (is_staff | can_view)

        QuerySet filtering (efficient, database-level):
            >>> from openedx.core.djangoapps.content_libraries.models import ContentLibrary
            >>>
            >>> # Gets all libraries user can view in a single SQL query
            >>> visible_libraries = perms['libraries.view'].filter(
            ...     request.user,
            ...     ContentLibrary.objects.all()
            ... )

        Individual object checks:
            >>> library = ContentLibrary.objects.get(library_id='lib:DemoX:CSPROB')
            >>> if perms['libraries.view'].check(request.user, library):
            ...     # User can view this specific library
            ...     return render_library(library)

    Note:
        The scope identifiers in Casbin policies must match the values in your
        Django model's scope_field. For example, if Casbin stores
        'lib:DemoX:CSPROB' and your model has library_id='lib:DemoX:CSPROB',
        they must match exactly (including format and casing).
    """

    def __init__(self, action_external_key: str, filter_keys: list[str] = ["org", "slug"]):
        """Initialize the rule with the action and filter keys to filter on.

        Args:
            action_external_key (str): The action/permission to check (e.g., 'view', 'edit').
            filter_keys (list[str]): The model fields to filter on when building QuerySet filters.
                Defaults to ['org', 'slug'] for ContentLibrary.
        """
        self.action_external_key = action_external_key
        self.filter_keys = filter_keys

    def query(self, user):
        """Convert this rule to a Django Q object for QuerySet filtering.

        This method enables efficient database-level filtering by:
        1. Querying the authorization system to get ALL library scopes where the user has this permission
        2. Parsing the library keys (org/slug pairs) from the scopes
        3. Building a Django Q object that filters for libraries matching those org/slug combinations

        This avoids N+1 query problems by filtering at the database level rather
        than checking permission for each object individually.

        Args:
            user: The Django user object (must have a 'username' attribute).

        Returns:
            Q: A Django Q object that can be used to filter a QuerySet.
               The Q object combines multiple conditions using OR (|) operators,
               where each condition matches a library's org and slug fields:
               Q(org__short_name='OrgA' & slug='lib-a') | Q(org__short_name='OrgB' & slug='lib-b')

        Example:
            >>> # User has 'view' permission in scopes: ['lib:OrgA:lib-a', 'lib:OrgB:lib-b']
            >>> rule = HasPermissionInContentLibraryScope('view', filter_keys=['org', 'slug'])
            >>> q = rule.query(user)
            >>> # Results in: Q(org__short_name='OrgA', slug='lib-a') | Q(org__short_name='OrgB', slug='lib-b')
            >>>
            >>> # Apply to queryset
            >>> libraries = ContentLibrary.objects.filter(q)
            >>> # SQL: SELECT * FROM content_library
            >>> #      WHERE (org.short_name='OrgA' AND slug='lib-a')
            >>> #         OR (org.short_name='OrgB' AND slug='lib-b')
        """
        scopes = get_scopes_for_user_and_permission(
            user.username,
            self.action_external_key
        )

        library_keys = [scope.library_key for scope in scopes]

        if not library_keys:
            return Q(pk__in=[])  # No access, return Q that matches nothing

        # Build Q object: OR together (org AND slug) conditions for each library
        query = Q()
        for library_key in library_keys:
            query |= Q(org__short_name=library_key.org, slug=library_key.slug)

        return query

    def check(self, user, instance):
        """Check if user has permission for a specific object instance.

        This method is used for checking permission on individual objects rather
        than filtering a QuerySet. It extracts the scope from the object and
        checks if the user has the required permission in that scope via Casbin.

        Args:
            user: The Django user object (must have a 'username' attribute).
            instance: The Django model instance to check permission for.

        Returns:
            bool: True if the user has the permission in the object's scope,
                  False otherwise.

        Example:
            >>> rule = HasPermissionInScope('view')
            >>> can_view = rule.check(user, library)
            >>> # Checks if user has 'view' permission in scope 'lib:DemoX:CSPROB'
        """
        return is_user_allowed(user.username, self.action_external_key, str(instance.library_key))


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
if settings.FEATURES.get('ENABLE_CREATOR_GROUP', False):
    perms[CAN_CREATE_CONTENT_LIBRARY] = is_global_staff | (is_user_active & is_course_creator)
else:
    perms[CAN_CREATE_CONTENT_LIBRARY] = is_global_staff

# Is the user allowed to view the specified content library in Studio,
# including to view the raw OLX and asset files?
CAN_VIEW_THIS_CONTENT_LIBRARY = 'content_libraries.view_library'
perms[CAN_VIEW_THIS_CONTENT_LIBRARY] = is_user_active & (
    # Global staff can access any library
    is_global_staff |
    # Libraries with "public read" permissions can be accessed only by course creators
    (Attribute('allow_public_read', True) & is_course_creator) |
    # Users can access libraries within their authorized scope (via Casbin/role-based permissions)
    HasPermissionInContentLibraryScope("view_library") |
    # Fallback to: the user must be part of the library's team (legacy permission system)
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
