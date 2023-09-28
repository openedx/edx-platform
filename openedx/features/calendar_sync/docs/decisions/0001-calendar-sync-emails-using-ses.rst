1. Amazon SES for calendar sync emails
================================================

Status
------

Proposed

Context
-------

For calendar sync functionality, we would like to send users
emails with .ics file attachments, which will in turn allow the user
to easily add/update course deadline dates on their personal calendars.

Decision
--------

We will use Amazon SES to send these emails.  Originally, we had hoped to use
Sailthru, but found that file attachments were not supported.  While emails
with attachments are not currently sent from platform at the time this doc is
being written, they are however sent from other services such as
enterprise-data using Amazon SES.  We will use a similar approach for our
calendar sync feature.
