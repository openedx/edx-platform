Instructor Dashboard AuthZ
##########################

Integration of the Instructor Dashboard (``/api/instructor/v2``) with ``openedx-authz``.

What it contains
****************

- ``constants.py``: the permission identifiers. Do not repeat the strings in the code. TEMPORARY: the permissions not defined by openedx-authz depend on a separate issue and are declared here only for testing.
- ``helpers.py``: ``user_has_instructor_permission`` and ``get_instructor_authz_permissions``.
- ``permissions.py``: ``InstructorAuthzPermission``, the DRF permission class for the views.
- ``legacy.py``: the pre-RBAC check equivalent to each permission.
- ``tests/mixins.py``: ``InstructorAuthzTestMixin`` to assign AuthZ roles in tests.

Behavior
********

It is driven by the ``authz.enable_course_authoring`` waffle flag, evaluated per course, with the same semantics as Studio:

- **Flag enabled:** only AuthZ is consulted. Legacy roles are ignored (openedx-authz already grants the global staff and superuser bypass).
- **Flag disabled:** only the legacy check runs, so the previous behavior is unchanged.

Every decision is logged with the path that resolved it (``authz`` or ``legacy``) in ``access_path``.

Migrating a view
****************

Replace ``InstructorPermission`` by ``InstructorAuthzPermission`` and declare the AuthZ permission next to the legacy one:

.. code-block:: python

    from lms.djangoapps.instructor.authz import constants as authz_constants
    from lms.djangoapps.instructor.authz.permissions import InstructorAuthzPermission

    class MyView(APIView):
        permission_classes = (IsAuthenticated, InstructorAuthzPermission)
        # A permission, or a mapping such as {"GET": ..., "POST": ...}.
        authz_permission = authz_constants.COURSES_VIEW_ENROLLMENTS
        # The legacy bridgekeeper permission.
        permission_name = permissions.VIEW_ENROLLMENTS

When the legacy rule is not a bridgekeeper permission, define ``legacy_permission_check(user, course_key)`` on the view. To check a permission in other code use ``user_has_instructor_permission``.
