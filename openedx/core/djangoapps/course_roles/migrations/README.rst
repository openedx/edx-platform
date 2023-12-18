Course Roles Migrations
#############################

To rollback the 0001_initial migration for course roles some manual steps are required.

First run the migration zero command to rollback all migrations.
Inside LMS or CMS shell:

 ./manage.py lms --settings=devstack_docker migrate course_roles zero

Migration 0001_initial will fail with the following error:

 django.db.utils.OperationalError: (1553, "Cannot drop index 'unique_role_permission': needed in a foreign key constraint")

Now we need to enter in the MySql80 container shell and run:

 mysql

The following SQL statements should be run on the mysql shell to be able to remove some indexes.

 CREATE INDEX permission_id ON edxapp.course_roles_rolepermission(permission_id);

 CREATE INDEX role_id ON edxapp.course_roles_rolepermission(role_id);
 
 CREATE INDEX role_id ON edxapp.course_roles_roleservice(role_id);
 
 CREATE INDEX service_id ON edxapp.course_roles_roleservice(service_id);
 
 CREATE INDEX user_id ON edxapp.course_roles_userrole(user_id);
 
 CREATE INDEX course_id ON edxapp.course_roles_userrole(course_id);
 
 CREATE INDEX role_id ON edxapp.course_roles_userrole(role_id);

Then in the LMS or CMS shell run the migration zero command again:

 ./manage.py lms --settings=devstack_docker migrate course_roles zero