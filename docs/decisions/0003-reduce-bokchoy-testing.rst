Status
======
Accepted


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
  * On a Daily cadence for 1 month.

#. Assess Impact of change.

  * We'll record the number of issues that bokchoy would have detected, when we manually run the bokchoy job out-of-band.
    * Both True issues and false positives(flakiness).


Outcome: Decision on whether or not to reduce the number of bokchoy tests.

Experiment Results
==================

Bokchoy tests were disabled for PRs for 3 weeks.  In that time only one change went out that was not caught by other test suites.  The change in question did not impact edx.org and was specific how configuration is read into the system.  The bokchoy tests did not detect any other failures that were not caught by other tests.  The `PR` where we monitored Bokchoy daily has more specific details.

.. _PR: https://github.com/edx/edx-platform/pull/23682

Decision
========

We initially used the a11y suite as a placeholder for a set of reduced tests.  Given the results of the tests, we will not pull in any tests from the full bokchoy suite and only keep the a11y tests.

Consequences
============

* Bokchoy testing infrastructure will remain off
* Bokchoy tests jobs will be removed all together rather than just disabled
* All bokchoy code in edx-platform not related to the a11y tests will be removed
* Testing Strategy for UI that is not part of a microfrontend
  * end-to-end smoke tests via the e2e-tests suite should only be for critical happy paths
  * UI and frontend logic should be tested using UI unit tests(currently Jasmine).
  * Django backends and rendered HTML should be tested with integration tests that use the `Django test client`

.. _Django test client: https://docs.djangoproject.com/en/2.2/topics/testing/tools/#the-test-client
