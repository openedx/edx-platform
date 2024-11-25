Status: Maintenance

Responsibilities
================
<<<<<<< HEAD
The Certificates app is responsible for creating and managing course run certificates, including relevant data models for invalidating certificates and managing the allowlist.

Direction: Move and Extract
===========================
Certificates related functionality is scattered across a number of places and should be better consolidated. Today we have:

* ``lms/djangoapps/certificates``
* ``openedx/core/djangoapps/certificates``
* ``cms/djangoapps/contentstore/views/certificates.py``
* Various front-end static templates in multiple locations

Ideally, we want to extract these into the `credentials service`_, which would be ultimately responsible for Course-Run and Program certificates (and possibly other credentials). Right now, the `credentials service`_ only manages Program certificates.

.. _credentials service: https://github.com/openedx/credentials

Glossary
========

More Documentation
==================
=======
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

>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
