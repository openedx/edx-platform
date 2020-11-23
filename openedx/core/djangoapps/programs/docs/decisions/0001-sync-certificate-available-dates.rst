Sync certificate_available_date and visible_date for certificates
=================================================================

Status
------

Review

Context
-------

In the Credentials service, certificate_available_date is called visible_date.
Whenever a generatedCertificate is updated or saved the first time, it sets
the visible date to certificate available date (available in studio settings).

There is a limitation in our code, if course team decides to change the
certificate_available_date it is not reflected in the credentials service
for all the certificates that were awarded before that change and have been
pushed to credentials service. The certificates' dates need to be in sync on
both places.

This has caused problems when a learner is able to see the certificate on
their dashboard but the change is not reflected on their learner record in
credential service.

Decision
--------

Whenever a CourseUpdate is made with change to the certificate_available_date,
the system updates the certificate visible_date on the credential service.

To achieve this, a signal is created to listen to any course update signal that
contains change in certificate_available_date and start a task to compute all
certificates that have been issued.

We will then reuse the award_course_certificate task for every certificate user
and get their visible_date updated on credential service to keep dates in sync
on both ends.


Consequences
------------

The system will have to process each issued user certificate and update the
visible_date for all of them individually as visible_date is an attribute for
every UserCredential object on credential service.
