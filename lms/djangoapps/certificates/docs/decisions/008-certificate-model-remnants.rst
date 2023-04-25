Leaving PDF Certificate Fields in Certificates Model
====================================================

Status
------

Accepted

Context
-------

As part of the `deprecation of PDF certificates`_, we had to make a decision about the future of several existing fields in
the ``GeneratedCertificate`` model that would no longer be used by the UI code. The replacement for PDF certificates is
web/HTML certificates, which have been outlined in a `previous ADR`_.


.. _deprecation of PDF certificates: https://github.com/openedx/public-engineering/issues/27
.. _previous ADR: https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/certificates/docs/decisions/003-web-certs.rst

Decision
--------

We decided to leave the existing fields ``download_url``, ``download_uuid``, and ``error_reason`` within the ``GeneratedCertificate``
model and did not remove them as part of our deprecation process where we removed the UI to display them.


Consequences
------------

A consequence of this decision is that all Open edX operators, including edx.org, will continue to store this data in their databases,
even though it does not have any functional use. 

Several pieces of code still reference these fields, and there are events that still pass around the download_url, even though this field
should no longer be populated or used any longer.


Alternatives Considered
-----------------------

We considered removing these fields and all associated code, but it was felt as though it was going to be too complex, because it involved
migrations and several API changes in order to support the removal.

We also felt as though it would be useful for operators that did have historical PDF certificates to continue to have a historical record of
where the PDF certificates were stored.
