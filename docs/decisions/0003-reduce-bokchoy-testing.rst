Status
~~~~~~
Draft


Context
~~~~~~~

edx-platform bokchoy tests are slow, flaky and difficult to debug.  A quick assessment of their value shows that they might be more trouble than they are worth.  And that we might get the same benefit with far fewer tests.

Baseline Data:(Last 7 days)
---------------------------

    Total number of builds: 253(across 106 PRs)

    Failures: 49(across 24 PRs)
        True Failures: 10(across 6 PRs)
        Failures that wouldn’t be caught by other test: 3(on 1 PR)

Color
=====

    Of the real failures found, there was one PR which had a failure that was only found via bokchoy and a115 tests.
        - This PR made a JS change which would have broken many pages from loading.

Recommendation
--------------

    As an experiment, we should not run bokchoy tests but continue to run a11y tests which will reduce the total number of tests significantly but continue to act as a smoke test for issues that can be caused by the fact that our frontend in edx-platform is still quite highly coupled together.

    We'll run in this mode for a month while we collect more data according to the test plan below.  This should give us either the confidence to significantly reduce the number of bokchoy tests or good reasons not to.

Test Plan
=========

    1. Deactivate bokchoy tests on master and all PRs but leave a11y tests running.
        - The a11y tests will act as a proxy for the small number of UI tests that would catch most major issues.

    2. Collect data on which issues bokchoy would have caught by running them manually font-of-band).
        - On a Daily cadense for 1 month.

    3. Assess Impact of change.
        - We'll record the number of issues that bokchoy would have prevented.
          - Both True issues and false positives(flakiness).


Outcome: Decision on whether or not to reduce the number of bokchoy tests.

Experiment Results
------------------

TBD

Consequences
------------

TBD

