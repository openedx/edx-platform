Django Secret Key Usage
-----------------------

Status
======

Accepted

Context
=======

Django's Secret key is used by django to cryptographically sign various
capabilities in django.  It is also used by the edx-platform in various cases
as a `pepper`_ when hashing data to anonymize it while keeping it consistent.
Some of the uses of the ``SECRET_KEY`` in edx-platform were not resilient to
the key being rotated.  As a part of ARCHBOM-1646 those code paths are being
updated so that regular rotation of the ``SECRET_KEY`` will cause temporary
issues but will not fully break things.  ie. Sessions might get invalidated or
data might not be corelatable over the change boundry but the change is
otherwise safe.

.. _pepper: https://en.wikipedia.org/wiki/Pepper_(cryptography)

Decisions
=========

1. Any uses of ``SECRET_KEY`` should be resilient to that key being rotated.

2. Wherever the secret key is used, it should also document the impact of
   rotating the key.

For example:

    Exposure of secret could result in identifying the tracking data for users
    if their actual session keys are also known; rotation is a one-time
    discontinuity in tracking metrics and should be accompanied by a heads-up
    to data researchers
