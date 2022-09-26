Status: Maintenance

Responsibilities
================
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
