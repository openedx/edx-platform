Testing Plans
#############

Testing plans have been considered, but the information presented here is a **collection of thoughts** and **not** a definitive **plan**.

Testing on staging
******************

* A test should be run before any roles are migrated. 
    * The goal is to confirm adding permissions checks has had no impact on user experience/access.
    * Role assignment in ``CourseRoles`` for the django admin dashboard should be tested at this time.
* A test should be run on staging for each role migrated or created in ``CourseRoles``. 
    * The goal is to confirm the role grants the appropriate level of access.
* A test should be run on staging for the assignment of each role.
    * The goal is to confirm the role can be assigned to users on the course level in the correct service(s) - LMS, CMS, or both.
    * Role assignment in the django admin dashboard will have already been tested.
* The tests for a role's functionality and assigning a role should be completed separately.
    * The goal is to ensure a role functions properly before any user is assigned the role.
    * This will also allow for dual streams of work.

Beta Testing on production
***************************

* Similar tests should be run on production with a select set of beta testers.
* It may be necessary to remove a beta testers ``StudentCourseAccessRole`` role when their new ``CourseRoles`` role is added.
    * The goal is to ensure they are not being granted access due to their original role, but through their new role.
* Creating new users for testing purposes should be considered.
    * The goal is to ensure full understanding of the permissions granted by the role and limit the risk of access being granted from previous roles or user attributes (i.e. is_staff).
* A lenth of time for beta testing was not determined, but it will likely vary per role and decrease as more roles have been migrated.
