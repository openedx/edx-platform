Add a new Django application for learner recommendations
========================================================

Status
------
Pending

Context
-------
Recommendations are shown on dashboard but we are planning on expanding the recommendations to other areas of the platform including course about pages on marketing site, course completion pages, payment page etc. Currently there is no dedicated space for the recommendations code.

- The recommendation relies heavily on the user model, course enrollments, catalog utils apps for course data. Vanguards are also looking to use user profile data for education and region based recommendations.
- The recommendation code is duplicated and scattered around different places. For learner dashboard, the same utility code exists in the learner_home and learner_dashboard app and with new recommendation APIs coming in we wanted to keep the code in one place.
- Recommendations are expected to be a core part of the user experience.

Keeping all of this context in mind the best way to organize recommendations is to create a new Django app that can be used by all the platform apps.


Decision
--------
Add a new Django application in lms for learner recommendations

Consequences
--------
* Adding a new Django app in lms
