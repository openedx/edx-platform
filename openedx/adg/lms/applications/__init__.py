"""
This app adds the ability to submit, review and manage applications for users and managers.

Application hub
------------
ADG provides an application hub where users (learners) can go and submit application for review.
Each user can submit only one application. Application submission process on Application hub
consists of two mandatory steps i.e. prerequisite courses and written application.

Prerequisite courses
------------
Application hub shows (configured) courses in its dashboard which are mandatory to pass in order to submit
the application. There are two type of mandatory courses: Program specific prerequisite courses and the business line
specific prerequisite courses.

Written application
------------
Written application is another mandatory step to submit the application. It asks the applicant few questions from
various sections including, contact information, education and business line/unit to apply to. All the data is saved in
the database.

Admin Dashboard
------------
ADG and BU admins can access limited but related models only, via admin dashboard, which is a subset of Django
admin view. ADG admins can view and manage all applications, however, BU admins can only manage applications
related to specific business line/unit.

With each business line there is a Django user group attached, which is used to create business unit specific
admins, though there are ADG admins as well. All types of admin are listed below:

1. Django admin (Super user)
1. ADG admin
3. Business unit (BU) admin

Multilingual courses
------------
Each course can exist in multiple languages. To manage this, multilingual course group is used. It is a model
in database which links group of same courses; one course per language. For example two courses with different
course id's but same content in different languages i.e. "Fundamentals of Environment", added in a group makes
one prerequisite course. Application hub will show course in specific language based on user's preferred language.
"""
default_app_config = 'openedx.adg.lms.applications.apps.ApplicationsConfig'
