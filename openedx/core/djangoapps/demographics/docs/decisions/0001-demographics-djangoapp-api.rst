Django Application to Support Demographics Features
---------------------------------------------------


Status
======

Accepted

Context
=======

To support demographics features and the IDA we need to be able to access the
current state of a User from the LMS (i.e. Program Enrollments, Enterprise status).

Decisions
=========

* To meet this need we are creating the Demographics Django Application in the
Open edX core. This application will contain utilities and APIs that will support
the Demographics feature set until they are replaced with other more general APIs
or no longer needed.
