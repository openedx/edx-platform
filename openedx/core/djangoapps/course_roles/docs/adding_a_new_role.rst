Adding a New CourseRoles Role
#############################

* The initial roles created in the CourseRoles service will match the existing StudentCourseAccessRole roles.
* These roles will be created with database migrations as they should exist in all instances.
* Future roles can be created using a database migration file if they are intended for all instances. 
* Future roles intended for only one instance can currently be created by running SQL.
* If creating new roles is a common use case, it can be added to the django admin dashboard.

Data Model Considerations
*************************

Data will need to be added to the Role, RolePermission, and RoleService tables.
This will create a role, grant it access, and determine which UI can be used to assign the role to a user.

Sample SQL
**********

Role Creation
-------------

The sql to create a new role is:

*insert into course_roles_role (name) values ([role_name]);* 

* This sql will create a role, but until it is connected to a permission or permissions it will not grant any access.
* This sql will create a role, but until it is connected to a service or services it will not be possible to assign the role to a user in a UI (including the admin dashboard). 

RolePermission Creation
-----------------------

The list of permissions to be connected to a role and their ids can be found by running the following sql:

*select * from course_roles_permission;* 

The sql to connect a role to the chosen permission is:

*insert into course_roles_rolepermission (role_id, permission_id) values ([role_id], [permission_id]);* 

RoleService Creation
--------------------

The list of services to be connected to a role and their ids can be found by running the following sql:

*select * from course_roles_service;*

The sql to connect a role to the chosen service is:

*insert into course_roles_roleservice (role_id, service_id) values ([role_id], [service_id]);*
