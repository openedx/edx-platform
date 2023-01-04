Core Versus Experimental Code
--------------

Status
======

Approved

Context
=======

One of the goals of the new Learner Home is to provide entry points for experimentation of different features. For example, the frontend offers a separate sidebar widget for showing a user their recommended courses.

In general, it is expected that these experiments will *NOT* modify or impact the core page functionality, showing a user their current enrollments / entitlements.

Decisions
=========

Any experiments, functionalities that are not necessarily tied to the core functionality of the page, should not modify the main `init` call that delivers user enrollment / entitlement data but instead exist as separate views / APIs, ideally in separate folders under `learner_home`.

This is both to avoid code bloat and protect the core functionality of Learner Home against bugs, outages, or regressions from experimental add-ons.

Consequences
============

By separating experimental / add-on code from the core page functionality, breaks or regressions introduced by experiments are expected to only impact containers / widgets which rely on that experimental code, leaving core functionality relatively stable and reliable.

While this is expected to increase the number of files / folders to keep track of inside of the `learner_home` app, the separation of files by functionality is expected to decrease cognitive load by making files / views more single-purpose and targeted.

Alternatives
============

1. Allow experimental code to live in the same files as core functionality. This is not so bad but increases the size and complexity of files and increases cognitive load while developing / debugging.
2. Allow experimental code to graft on to core functionality. We want to avoid this as it will necessarily slow the pace of experimentation and increase the need to regression test any experimental changes to avoid breaking core functionality.
