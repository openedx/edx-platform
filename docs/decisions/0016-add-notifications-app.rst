Add new Django application for notifications
==================================================

Status
------
Accepted

Context
-------
We are planning to build a notification framework that can be leveraged by platform apps/workflows like forums, grading, announcements, reminders, marketing and course recommendations etc. We intend to implement this framework using forum notifications, and later expand it to other platform apps/areas.
The notification framework has a lot of platform dependencies e.g the User model, User account settings etc. This is expected to be a core feature of the platform and will be enabled by default for all users.
Keeping all of this context in mind the best way to implement this feature is to create a new Django app that can be used by all the platform apps.



Decision
--------
Add a new Django application in lms for notifications

Consequences
--------
* adding a new Django app in lms
