Library User role
#################

Description - Current State
***************************

library_user role
-----------------

* The library_user role in the student_course_access_role service is used to assign access to a library.
* The library is stored as the "course" in the data model.

v2 Content Libraries
--------------------

* v2 Content Libraries is an ongoing project to modernize the content libraries data structures.
* Once completed, v2 Content Libraries will no longer utilize student_course_access_role to control access.

course_role data structures
---------------------------

* The database model for course_role uses a foreign key for the course_id when assigning a role to a user.
* The foreign key usage means that a library cannot be considered a "course" for role assignments that utilize course_role.


Potential Options
*****************

Below is a list of options discussed for migrating from student_course_access_role to course_roles in regards to the library_user role.

1. library_user is not migrated to course_roles.
    * The library_user role will continue to be used from within the student_course_access_role service.
    * Once all content libraries have been migrated to v2 content libraries, the library_user role will no longer be needed.
    * At this time, the final deprecation of student_course_access_role can occur.

2. A new permissions based service is created for access to non-course objects.
    * Access will initially be for content libraries, but could be expanded to other objects as needed.
    * The set of permissions in the new service will match those created for course_roles.

Option 1 is currently the option that will be implemented,
but a decision will not be finalized until migration for course_roles has begun.
The major determinant is the progress on the v2 Content Libraries.


