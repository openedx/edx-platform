Status: Maintenance

Responsibilities
================
The Certificates app is responsible for creating and managing course certificates, including
certificate settings, course certificate templates, and generated learner course certificates.
The app includes  relevant data models for invalidating certificates and managing the allowlist.

See Also
========
Course Certificates related functionality is scattered across a number of places:

* ``lms/djangoapps/certificates``
* ``openedx/core/djangoapps/credentials``
* ``cms/djangoapps/contentstore/views/certificates.py``
* Various front-end static templates in multiple locations

See also the `credentials service`_, which is the system of record for a learner's Program Certificates.

.. _credentials service: https://github.com/openedx/credentials

