Fixing the Quality and JS checks
################################

Status
******

Accepted

Implemented by https://github.com/openedx/edx-platform/pull/35159

Context
*******

edx-platform PRs need to pass a series of CI checks before merging, including
but not limited to: a CLA check, various unit tests, and various code quality
tests. Of these checks, two checks were implemented using the "Paver" Python
package, a scripting library `which we have been trying to move off of`_. These
two checks and their steps were:

* **Check: Quality others**

  * **pii_check**: Ensure that Django models have PII annotations as
    described in `OEP-30`_, with a minimum threshold of **94.5%** of models
    annotated.
  * **stylelint**: Statically check sass stylesheets for common errors.
  * **pep8**: Run pycodestyle against Python code.
  * **eslint**: Statically check javascript code for common errors.
  * **xsslint**: Check python & javascript for xss vulnerabilities.
  * **check_keywords**: Compare Django model field names against a denylist of
    reserved keywords.

* **Check: JS**

  * **test-js**: Run javascript unit tests.
  * **coverage-js**: Check that javascript test coverage has not dropped.

As we worked to reimplement these checks without Paver, we unfortunately
noticed that four of those steps had bugs in their implementations, and thus
had not been enforcing what they promised to:

* **pii_check**: Instead of just checking the result of the underlying
  code_annotations command, this check wrote an annotations report to a file,
  and then used regex to parse the report and determine whether the check
  should pass. However, the check failed to validate that the generation of the
  report itself was successful. So, when malformed annotations were introduced
  to the edx-proctoring repository, which edx-platform installs, the check
  began silently passing.

* **stylelint**: At some point, the `stylelint` binary stopped being available
  on the runner's `$PATH`. Rather than causing the Quality Others check to
  fail, the Paver code quietly ignored the shell error, and considered the
  empty stylelint report file to indicate that there were not linting
  violations.

* **test-js**: There are eight suites within test-js. Six of them work fine.
  But three of them--specifically the suites that test code built by Webpack--
  have not been running for some unknown amount of time. The Webpack test build
  has been failing without signalling that the test suite should fail,
  both preventing the tests from runnning and preventing anyone from noticing
  that the tests weren't running.

* **coverage-js**: This check tried to use `diff-cover` in order to compare the
  coverage report on the current branch with the coverage report on the master
  branch. However, the coverage report does not exist on the master branch, and
  it's not clear when it ever did. The coverage-js step failed to validate that
  `diff-cover` ran successfully, and instead of raising an error, it allowed
  the JS check to pass.

Decision & Consequences
***********************

pii_check
=========

We `fixed the malformed annotations`_ in edx-proctoring, allowing the pii_check
to once again check model coverage. We have ensured that any future failure of
the code_annotations command (due to, for example, future malformed
annotations) will cause the pii_check step and the overall Quality Others check
to fail. We have stopped trying to parse the result of the annotations report
in CI, as this was and is completely unneccessary.

In order to keep "Quality others" passing on the edx-platform master branch, we
lowered the PII annotation coverage threshold to reflect the percentage of
then-annotated models: **71.6%**. After a timeboxed effort to add missing
annotations and expand the annotation allowlist as appropriate, we have managed
to raise the threshold to **85.3%**. It is not clear whether we will put in
further effort to raise the annotation threshold back to 95%.

This was all already `announced on the forums`_.

stylelint
=========

We have removed the **stylelint** step entirely from the "Quality Others"
check. Sass code in the edx-platform repository will no longer be subject to
any static analysis.

test-js
=======

We have stopped running these Webpack-based suites in CI:

* ``npm run test-lms-webpack``
* ``npm run test-cms-webpack``
* ``npm run test-xmodule-webpack``

We have created a new edx-platform backlog issue for
`fixing and re-enabling these suites`_.
It is not clear whether we will prioritize that issue, or instead prioritize
deprecation and removal of the code that those suites were supposed to be
testing.

coverage-js
===========

We will remove the **coverage-js** step entirely from the "JS" check.
JavaScript code in the edx-platform repository will no longer be subject to any
unit test coverage checking.

Rejected Alternatives
*********************

* While it would be ideal to raise the pii_check threshold to 94.5% or even
  100%, we do not have the resources to promise this.

* It would also be nice to institute a "racheting" mechanism for the PII
  annotation coverage threshold. That is, every commit to master could save the
  coverage percentage to a persisted artifact, allowing subsequent PRs to
  ensure that the pii_check never returns lower than the current threshold. We
  will put this in the Aximprovements backlog, but we cannot commit to
  implementing it right now.

* We will not fix or apply amnestly in order to re-enable stlylint or
  coverage-js. That could take significant effort, which we believe would be
  better spent completing the migration off of this legacy Sass and JS and onto
  our modern React frontends.


.. _fixing and re-enabling these suites: https://github.com/openedx/edx-platform/issues/35956
.. _which we have been trying to move off of: https://github.com/openedx/edx-platform/issues/34467
.. _announced on the forums: https://discuss.openedx.org/t/checking-pii-annotations-with-a-lower-coverage-threshold/14254
.. _OEP-30: https://docs.openedx.org/projects/openedx-proposals/en/latest/architectural-decisions/oep-0030-arch-pii-markup-and-auditing.html
.. _fix the malformed annotations: https://github.com/openedx/edx-proctoring/issues/1241
