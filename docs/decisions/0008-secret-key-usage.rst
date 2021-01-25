Django Secret Key Usage
-----------------------

Status
======

Pending

Context
=======

Django's Secret key is used by Django to cryptographically sign various
capabilities in Django.  It is also used by the edx-platform in various cases
as a `pepper`_ when hashing data to anonymize it while keeping it consistent.
Some of the uses of the ``SECRET_KEY`` in edx-platform were not resilient to
the key being rotated.  As a part of ARCHBOM-1646 those code paths are being
updated so that regular rotation of the ``SECRET_KEY`` will cause temporary
issues but will not fully break things.  ie. Sessions might get invalidated or
data might not be correlatable over the change boundary but the change is
otherwise safe.

.. _pepper: https://en.wikipedia.org/wiki/Pepper_(cryptography)

Decisions
=========

1. Any uses of ``SECRET_KEY`` should be resilient to that key being rotated.

2. Wherever the ``SECRET_KEY`` is used, it should also document the impact of
   rotating the key.

    For example:

    Rotation is a one-time discontinuity in tracking metrics and should be
    accompanied by a heads-up to data researchers

3. Whenever the ``SECRET_KEY`` is used, it should also document the
   consequences of the key being exposed.

    For example:

    Exposure of secret could result in identifying the tracking data for users
    if their actual session keys are also known

Consequences
============

- The ``SECRET_KEY`` should only be used in cases where rotation can be done
  quickly.  Because the secret is shared, not changing it quickly can expose
  multiple features to attack if any one usage is more expensive to rotate than others.
  If you are considering using the ``SECRET_KEY`` in a situation where the act
  of rotation will be expensive (time, coordination, preparation) you should
  instead consider using a new unique secret specific to your use case.
