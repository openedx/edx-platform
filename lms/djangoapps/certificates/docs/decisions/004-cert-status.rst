Course certificate Status
=========================

Status
------
Accepted

Background
----------
Course certificates can have any one of a number of status values (for the
full list, see the `CertificateStatuses model`_). For a certificate to be
available for the user to see, it must be in the *downloadable* state, meaning
it must have a status value of *downloadable*.

Decision
--------
The course certificate code will only set the following certificate statuses:

* downloadable - The user has been granted this certificate and the certificate is ready and available
* notpassing - The user has not achieved a passing grade
* unavailable - Certificate has been invalidated
* unverified - The user does not have an approved, unexpired identity verification

Other status values are kept for historical reasons and because existing course
certificates may have been granted that status.

Consequences
------------
If a certificate has been invalidated, its status will be *unavailable*.

If all requirements have been met, a *downloadable* certificate will be
generated (created or updated).

If all requirements *except* for identity verification have been met, an
*unverified* certificate will be generated.

If all requirements *except* for passing the course have been met and a
certificate already exists, its status will be *notpassing*. Alternately, if a
*downloadable* certificate exists and a failing grade signal is received for
a user who is not on the allowlist, the certificate's status will be
*notpassing*.

Note that this does not create a hierarchy of certificate statuses. For
example, a certificate could have a *notpassing* status even if the user
has not the passed identity verification requirement.

References
----------
For a full list of requirements for a course certificate to be granted, please
see the `allowlist certificate requirements`_ and `certificate requirements`_.

For a full list of certificate statuses, see the `CertificateStatuses model`_.

.. _allowlist certificate requirements: ./001-allowlist-cert-requirements.rst
.. _certificate requirements: ./002-cert-requirements.rst
.. _CertificateStatuses model: ../../data.py
