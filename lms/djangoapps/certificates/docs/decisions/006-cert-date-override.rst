Certificate Date Override
=========================

Status
------
Accepted

Background
----------
Generally speaking, a learner is awarded a course certificate upon earning a
passing grade in a course. (Other ADRs go into the specifics of when a
certificate is earned.) The data backing a course certificate is stored in the
``GeneratedCertificate`` model. The course certificate generally displays an
"Issued On" date. This date might be the associated course’s
``certificate_available_date`` if set and elapsed; otherwise it will be the
``GeneratedCertificate`` ``modified`` date.

However, the ``modified`` date can be advanced by several backend processing
systems. This means that a course certificate can display a confusing issue
date. When this date changes to a date that is significantly distanced from the
actual date that the learner earned the certificate, it can cause problems for
the learner if they have an outcome (raise, promotion, acceptance to academic
program) that is related to when they earned the certificate.


Decision
--------
We will add a new model to the certificates app called
``CertificateDateOverride``. This model will be accessed through the Django Admin
and used to manually override the date on course certificates.

We are choosing to make a new, separate model and associate it with
``GeneratedCertificate`` (rather than adding new fields to ``GeneratedCertificate``)
because we expect the number of certificates that will need to use this feature
to be very low. We don’t want to add a new field to a potentially very large
table that may only be used by a small number of records.
``CertificateDateOverride`` will have a ``OneToOne`` Relationship with
``GeneratedCertificate``; each certificate should have only one date override, and
a date override will belong to only one certificate. The new table will have an
accompanying history table.

In addition to the date itself, we would like to keep track of some other pieces
of information around the date: the ``user`` who made the date override, and the
``reason`` why. While ``django-simple-history`` is able to provide us with these
things, we decided to keep this data directly on the ``CertificateDateOverride``
model to be able to surface them more directly in case the record is used in the
product UI in the future.

To edit or remove a date override, admin users should return to the relevant
``CertificateDateOverride`` admin page and either edit the date or delete the
record, respectively. This is a different approach than some analogous models in
our app, where data is "removed" by toggling an ``active`` flag. In our case, we
are comfortable truly deleting the ``CertificateDateOverride`` objects, and
comfortable relying on the history table’s record of change.

The ``CertificateDateOverride`` will override all other date logic when it comes
to the date displayed on the certificate. (This includes overriding the
``certificate_available_date``.) However, the ``CertificateDateOverride`` will not
affect the availability or visibility of the certificate.

Whenever a ``CertificateDateOverride`` is saved (either for the first time or
after a change) or deleted, it will trigger the ``COURSE_CERT_CHANGED`` signal.
The date override data (if present) will be included in the post to
`Credentials`_ whenever this signal is called. Credentials will save and use
this data for the Program Record page.

.. _Credentials: https://github.com/openedx/credentials
