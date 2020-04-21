Status
======
Draft


Context
=======

edx-platform bokchoy tests are slow, flaky and difficult to debug.  A quick assessment of their value shows that they might be more trouble than they are worth.  And that we might get the same benefit with far fewer tests.

Baseline Data:
--------------

This data was collected based on the results of bokchoy tests run across all edx-platform PRs over the last 7 days.

* Total number of builds: 253(across 106 PRs)
* Failures: 49(across 24 PRs)

  * True Failures: 10(across 6 PRs)
  * Failures that wouldn’t be caught by other test: 3(on 1 PR)

Color
~~~~~

Of the real failures found, there was one PR which had a failure that was only found via bokchoy and a11y tests.
    * This PR made a JS change which would have broken many pages from loading.

Recommendation
==============

Based on the info we have so far, we will only run a suite of smoke tests in bokchoy that ensure the frontend is not entirely broken.

For the experiment, we will use the a11y bokchoy tests as a simple stand-in for a suite of smoke tests, because it is already a much smaller suite of happy path tests.

During the experiment, if we find we are missing coverage via a regression, we will first add a missing Python or JavaScript unit test where possible.  Only if this isn't possible would we add to the smoke suite of bokchoy tests.

We'll run in this mode for a month while we collect more data according to the test plan below.  This should give us either the confidence to significantly reduce the number of bokchoy tests or good reasons not to.

Test Plan
---------

#. Deactivate bokchoy tests on master and all PRs but leave a11y tests running.

  * The a11y tests will act as a proxy for the small number of UI tests that would catch most major issues.

#. Collect data on which issues bokchoy would have caught by running them manually out-of-band from the standard CI/CD process.

  * We'll look at the failures on the out-of-band bokchoy job to find any true failures that would be caught by the removed tests.
  * On a Daily cadense for 1 month.

#. Assess Impact of change.

  * We'll record the number of issues that bokchoy would have detected, when we manually run the bokchoy job out-of-band.
    * Both True issues and false positives(flakiness).


Outcome: Decision on whether or not to reduce the number of bokchoy tests.

Experiment Results
==================

TBD

Decision
========

TBD - Based on experiment outcome.

Consequences
============

TBD

