Learner Dashboard
=================

This Django app hosts dashboard pages used by edX learners. The intent is for this Django app to include the following three important dashboard tabs:
 - Courses
 - Programs
 - Profile

Courses
---------------
The learner-facing dashboard listing active and archived enrollments. The current implementation of the dashboard resides in ``common/djangoapps/student/``. The goal is to replace the existing dashboard with a Backbone app served by this Django app.

Programs
---------------
A page listing programs in which the learner is engaged. The page also shows learners' progress towards completing the programs. Programs are structured collections of course runs which culminate into a certificate.

Implementation
^^^^^^^^^^^^^^^^^^^^^
The ``views`` module contains the Django views used to serve the Program listing page. The corresponding Backbone app is in the ``edx-platform/static/js/learner_dashboard``.

Configuration
^^^^^^^^^^^^^^^^^^^^^
In order to turn on the Programs tab, you need to update the ``Programs API Config`` object in the lms Django admin. Make sure you set the values ``Enabled``, ``Do we want to show program listing page`` and ``Do we want to show xseries program advertising`` to be true

Profile
---------------
A page allowing learners to see what they have accomplished and view credits or certificates they have earned on the edX platform.

