Learner Dashboard
=================

This Django app hosts the dashboard pages used primary by the edx learners. The intent is for this Django app to include the following three important dashboard tabs:
 - Courses
 - Programs
 - Profile

The complete functional vision is presented visually at https://projects.invisionapp.com/share/UP46LNKTK#/screens/101238377

Courses
---------------
This is the learner facing dashboard which shows the learner which courses they are currently enrolled into. The current implementation of the dashboard is in the `edx-platform/common/student/` django app. The idea is to completely re-construct the learner facing dashboard with a front-end app served from this django app.

Programs
---------------
The view to show our learners the list of programs they are currently enrolled into. This is a structured way to allow edx learner to build their experience on edX towards a credit or certificate

Implementation
^^^^^^^^^^^^^^^^^^^^^
The views.py file contains the view logic of the django app to serve the Program listing page. The front-end backbone app is written in the `edx-platform/static/js/learner_dashboard` folder

Profile
---------------
The view of the learner entity on edX. This view would allow learning to see what they have accomplished and view credits or certificates they have earned on the edX platform. It is also a place where the profile can be published to the external web services as a credential.
