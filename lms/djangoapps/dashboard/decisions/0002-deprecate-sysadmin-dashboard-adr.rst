2. Deprecating the Sysadmin Dashboard
---------------------

Status
------

Draft

Context
-------

Maintaining the sysadmin dashboard is challenging, and it is not widely used. The code is part of the lms
application, even though most of its use cases are relevant to course authoring.

The sysadmin dashboard would be better suited as a pluggable django application, using appropriate APIs in the
cms application

Decision
--------

In order to deprecate the sysadmin dashboard and move it to a pluggable django application, the followings APIs
would need to be added and/or moved into the cms application

1. Create a cms user account

   https://github.com/edx/edx-platform/blob/50dd1238408dc6785f022d8540961f96e0d6bb4f/lms/djangoapps/dashboard/sysadmin.py#L113-L151

2. Import a course from git

   https://github.com/edx/edx-platform/blob/master/lms/djangoapps/dashboard/git_import.py

3. Delete a course

   https://github.com/edx/edx-platform/blob/b4556a4bec/lms/djangoapps/dashboard/sysadmin.py#L344-L369


These APIs can be removed entirely, as they are adequately covered by existing functionality:

1. Delete a cms user.

   This functionality should be removed entirely. CMS user accounts should be retired using the existing `edX User
   Retirement Feature <https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/user_retire/>`_.

2. Staffing and Enrollment

   https://github.com/edx/edx-platform/blob/b4556a4bec/lms/djangoapps/dashboard/sysadmin.py#L380-L413

   This functionality may be redundant to features in the Insights application.


