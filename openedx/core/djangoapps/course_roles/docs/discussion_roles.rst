Discussion Roles / ``django_comment_client``
############################################

Description - Current State
***************************

* ``django_comment_client`` **roles** are **built with** ``django_comment_client`` **permissions**.
* ``django_comment_client_permission`` **checks** are found **in** the **code** base.
* ``django_comment_client_roles`` are assigned on a **course level** basis.
* **role checks** related to **discussion roles** are found **in** the **code** base.
* Some ``student_course_access`` **roles require access** to the **discussion** service.


Potential Options
*****************

1. Maintain ``django_comment_client`` as a separate service from course_roles.
    * 2 services would be responsible for granting course level access.
    * ``django_comment_client`` role checks could be updated to check for ``django_comment_client`` permissions. This would allow for easier creation of new discussion roles (ensure flexibility).
    * ``course_roles`` permissions would be used to grant access to discussions for ``course_roles`` roles.
2. Migrate ``django_comment_client`` roles to ``course_roles``
    * A single service would be responsible for granting course level access.
    * Additional permissions may need to be added to course_roles permissions to account for current ``django_comment_client`` permissions.
    * A refactor of the discussion service authorization related code may be needed depending on the permissions added to ``course_roles``.

A decision has not been reached on how to handle discussion roles. The primary goal of ``course_roles`` can be met with either solution.