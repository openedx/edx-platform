"""
'Webinars' is a Django app built as part of the ADG LMS and Admin experience.

Admin Experience
----------------

This feature enables ADG admins to:
 - create new events(the words 'event' and 'webinar' are used interchangeably) on the admin site
 - update existing events
 - cancel existing events
 - clone existing events
 - view all events i.e. upcoming, cancelled and delivered
 - view list of registered users against events

Learner Experience
------------------

It also enables ADG learners to:
 - view a list of upcoming events on the LMS site
 - view details of an event
 - register for an upcoming event and attend a webinar via an external link
 - cancel registration


Upon new event creation, invitations are sent via email. All registered users
 - can receive event update email
 - receive event cancellation email
 - receive automated reminder emails
"""

default_app_config = 'openedx.adg.lms.webinars.apps.WebinarsConfig'
