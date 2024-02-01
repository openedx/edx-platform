Project Scope
#############

Project Scope and Completion Information
****************************************

.. list-table::
   :widths: 70 15 15
   :header-rows: 1

   * - Project Task
     - Status (Completed, In Progress, To Do)
     - Required or Optional
   * - Architectural Planning
     - Completed
     - Required
   * - ``CourseRoles`` Model Setup
     - Completed
     - Required
   * - Update existing access control - add permission checks where roles are currently checked
     - Completed
     - Required
   * - Add additional access control - add permission checks in additional locations in the code
     - In Progress
     - Required
   * - Update CMS Course Team Design
     - To Do
     - Optional
   * - Turn code on in production
        - Test on staging that there are no changes to performance or user impacts
        - Beta test on production that there are no changes to performance or user impacts
        - Set waffle flag to true for all users or remove waffle flag checks from code
     - To Do
     - Required
   * - Add New CMS only role
     - To Do
     - Optional
   * - Migrate ``student_course_access_role`` roles to ``course_roles`` (see below for details)
     - To Do
     - Required
   * - Update or Migrate ``django_comment_client_role`` roles (see below for details)
     - To Do
     - Required
   * - Deprecate unused code
        - Track usage of ``student_course_access_role`` functions
        - Update code to remove uses of ``student_course_access_role`` functions
        - Remove ``student_course_access_role`` functions
        - Remove ``course_roles.user_permission_checks`` waffle flag
     - To Do
     - Required

Migrate student_course_access_role roles to course_roles
********************************************************

The following steps will need to be followed for each ``student_course_access_role`` that is being migrated to the ``course_roles`` service.
The library role will not be migrated. The ``student_course_access_role`` service will continue to be used for the library role.

- Create role in ``course_roles`` with DB script
- Use Django Admin Dashboard to assign role for testing
- Update code to assign role using ``course_roles`` on CMS Course Roles and LMS Membership page
- Remove role assignment from Django Admin Dashboard for ``student_course_access_role`` for specified role
- Use role assignment in production for set period of time confirming no issues are reported
- Write script to migrate data from ``student_course_access_role`` user assignment table to ``course_roles``


Update or Migrate django_comment_client_role roles
**************************************************

``django_comment_client_role`` roles are based upon permissions.
In some places in the code the ``django_comment_client`` permission values are checked.
In some places in the code the ``django_comment_client`` role or the ``student_course_access`` role values are checked.

Potential options include:

1. ``django_comment_client`` code is updated to always check permissions when checking access for a ``django_comment_client`` role.
2. migrate roles from ``django_comment_client`` to ``course_role``
