Deprecating code
################

* ``CourseRoles`` is inteded to be used **in place of** ``StudentCourseAccessRole``.
* ``StudentCourseAccessRole`` will be **deprecated** once ``CourseRoles`` is **fully implented** and being used in production.
* This deprecation must be completed **with care**.
* **Extra attention** will be needed for **services outside** ``edx-platform`` that may currently be using ``StudentCourseAccessRole``.

Potential Deprecation Steps
***************************

As each **role** and the associated **role assignments** are **migrated** to ``CourseRoles``, 
the **UI** and **admin dashboard UI** will be updated to **no longer be using** ``StudentCourseAccessRole`` for the **associated role**.
By the time **all roles** (and associated role assignments) have been **migrated**, the **expected usage** of ``StudentCourseAccessRole`` will be **low**.
Once that point has been reached, the following steps can be implemented 
to better understand remaining useage, notify developers about the planned deprecation, and deprecate the code.

Understanding Usage
--------------------

These notifications can be used to determine if any **services** are still **assigning roles** using ``CourseAccessRole``.

* Add **logging** (notify) in the the ``CourseAccessRole`` class in ``common/djangoapps/student/models/user.py``.
* Add **logging** (notify) in the ``CourseAccessRoleAdmin`` class in ``common/djangoapps/student/admin.py``.
* Add **UI notification** in the ``CourseAccessRoleAdmin`` class in ``common/djangoapps/student/admin.py``.

Notifying Developers
--------------------

Providing sufficient **notification to all developers in the community** will help ensure that the code isn't still in use when deprecated.

* Create a [DEPR] issue in https://github.com/openedx/public-engineering.
* Post to `Open edX Slack <https://app.slack.com/client/T02SNA1T6/C02SNA1U4>`_ and `Open edX Discussions <https://discuss.openedx.org/>`_

Deprecating the Code
--------------------

* **Remove code** in the ``CourseAccessRole`` class in ``common/djangoapps/student/models/user.py``.
* **Remove** the ``CourseAccessRoleAdmi`` class from ``common/djangoapps/student/admin.py``.

At this time, **no role checks** should be **needed**. Role checks should be removed from the code. 
There are comments in the code locations where the role checks should be removed. 
Once the **role checks** are **removed**, the process to **begin deprecating** the **code** that checks the roles can begin.

* **Remove role checks** code
* Add **logging** (notify) in ``common/djangoapps/student/roles.py``
* **Confirm** code is **not used** for a length of time, then **remove** the **code** in ``common/djangoapps/student/roles.py``.
* **Remove** ``course_roles.use_permission_checks`` waffle flag from **code**
* **Remove** ``course_roles.user_permission_checks`` flag from the **Django Admin** Dashboard (remove database record)

Open Questions Related to Code deprecation
******************************************

1. How can we ensure all xblocks are ready to check permissions instead of roles?
2. If xblock code needs the role checks, how can we ensure no other usages of roles checks sneak into the code?
3. How will the library_user role be handled? (see library_user_role.rst for more information)
4. How will the discussion roles be handled? (see discussion_roles.rst for more information)
5. How long should each step be in production before moving to the next step in the deprecation process?
6. Should the waffle flag be used to ignore/hide code for testing before removing the code for deprecation?
