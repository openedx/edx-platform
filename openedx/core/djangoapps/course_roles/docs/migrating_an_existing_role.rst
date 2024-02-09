Migrating a Role and Role Assignments to CourseRoles
####################################################

Migrating a Role
****************

Roles will be **migrated** from ``StudentCourseAccessRole`` to ``CourseRolesRole``.
Role migration is a technical process that **requires manual testing** between steps.
This process will need to be completed for **all** ``StudentCourseAccessRole`` roles, **except** the ``library_user`` role.

1. **Create role** in ``CourseRolesRole`` and **assign permissions** in ``CourseRolesRolePermission`` table by creating a **migration file** and merging to master branch.
2. Use **django admin** dashboard to **assign users** the **role** on **staging**.
3. Users **test expected workflow** for users with the role and confirm appropriate access.
4. If any **access changes** are **needed**, create **new migration** or **update code** to reflect correct access for a specific permission.
5. Use **django admin** dashboard on **production** to assign **beta testers** the role.
6. Users **test expected workflow** for users with the role and confirm appropriate access.
7. If any **access changes** are **needed**, review and **make updates**. This will **require re-testing** on **staging** as well.
8. **Update code** to **assign users** the role using ``CourseRoles`` in the **LMS** and **CMS** (depending on current location it is assigned). This will also include a **migration** to **assign** the role a **service** or services.
9. **Test** role assignment code on **staging** and then **production** using the **waffle flags**.
10. Set **waffle flag** to **true** for the role.
11. **Remove waffle flag** as technical debt as time allows.

Role Assignments
****************

Once a **role** has been **migrated** to ``CourseRoles`` **and** thouroughly **tested**, **user assignment migration** can occur.
**User's** are **assigned** a ``StudentCourseAccessRole`` **role** for a course or organization in the ``StudentCourseAccessRole`` database tables.
These **role assignments** will need to be **migrated** to the ``CourseRoles`` database schema.
A **script** can be written for this step to be **run for each role** on first **staging** and then **production** at the appropriate time.
The **script** will also need to be **included in** whichever **release** starts using ``CourseRoles`` so all instances can migrate their role assignments.

Technical Considerations for the Script
---------------------------------------

* The ``organization`` and ``course`` are **foreign keys** in ``CourseRoles``, but not in ``StudentCourseAccessRole``. 
* The ``course_id`` and ``organization_id`` can be **null**, but this represents a **significant data point**. Null should **not** be used for **unknonwn values**, but **only when** null is the **intended** value.
* **Script** should be **reusable** for different roles.
* Script should be **run one role at a time**, to migrate users to the new roles as the new roles are approved.

There is also the option to write one script to migrate all data once all roles are migrated to ``CourseRoles``.
This is not the current planned option. The current options were chosen to limit risk and front load value where possible.
