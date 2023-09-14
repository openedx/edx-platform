1. Course Level Roles
######################


Status
******

**Provisional** *2023-09-13*

The status will be updated to *Accepted* upon completion of reimplementation.

Context
*******

There is currently no single functionality being used by the majority of the codebases that are a part of Open edX
that allows for adding roles (permission sets) for a user at the course and organization level
that provides the flexibility to allow users to edit or create new roles (permission sets) that can be assigned to users.


Decision
********

Modified LMS table and solution - within LMS/CMS
------------------------------------------------
- We will add new tables to manage roles, permission, and groups of users that are assigned to roles.
- We will add additional tables, if necessary, to manage custom roles.
- We will create the new tables within the current DB schema and LMS/CMS repo.


Consequences
************

New tables diagrams:
-------------------

course_roles_permission
=======================
+======+
| id   |
| name |
+------+

course_roles_role
=================
+======+
| id   |
| name |
+------+

course_roles_rolepermissions
============================
+===============+
| id            |
| permission_id |
| role_id       |
+---------------+

course_roles_userrole
=====================
+===========+
| id        |
| user_id   |
| course_id |
| org_id    |
| role_id   |
+-----------+

course_roles_services
=====================
+======+
| id   |
| name |
+------+

course_roles_roleservice
========================
+============+
| id         |
| role_id    |
| service_id |
+------------+


Rejected Alternatives
*********************

Current LMS table and solution
------------------------------
**Overview:**
- Utilize the existing DB table (`student_courseaccessrole`) in the LMS schema to assign users to roles.
- Add additional tables as needed to manage roles, permission sets, and groups of users that are assigned to roles.
- Additional tables would need to be added to manage role permissions (to accommodate custom roles).
- The tables and code would live within the current LMS schema and LMS/CMS repo.

**Pros:**
- Builds upon current solution.
- Allows for flexibility of permission sets.
- Iterative - Does not require front-loading engineering work before seeing a “benefit” from the users point of view.

**Cons:**
- Only focuses on course level roles.
- Potential latency issues for LMS API calls (reason referenced for why edx-rbac is using cookies).
- Not distributed (removes currently existing positive aspect of edx-rbac).
- Adds code to mono-repo.
- There is a higher risk to negatively impact user experience when modifying in use code.


Modified Current LMS table and solution - new IDA
-------------------------------------------------
**Overview:**
- Utilize the concepts behind the existing course level roles (and db table), but creates the table structure in a separate db/schema.
- Begins creating an IDA for authorization.

**Pros:**
- Greatest amount of flexibility.
- Easy to create new roles and add custom roles.
- Users can be assigned groups that are assigned roles or be assigned roles directly.

**Cons:**
- Requires largest amount of work.
- Adds yet another (at least the fourth) way to add roles to Open edX.
- Requires large amount of work before initial value added.
