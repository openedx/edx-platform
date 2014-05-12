*******
Jenkins
*******

`Jenkins`_ is an open source continuous integration server. edX has a Jenkins
installation specifically for testing pull requests to our open source software
project, including edx-platform. Before a pull request can be merged, Jenkins
must run all the tests for that pull request: this is known as a "build".
If even one test in the build fails, then the entire build is considered a
failure. Pull requests cannot be merged until they have a passing build.

Kicking Off Builds
==================

Jenkins has the ability to automatically detect new pull requests and changed
pull requests on Github, and it can automatically run builds in response to
these events. We have Jenkins configured to automatically run builds for all
pull requests from core committers; however, Jenkins will *not* automatically
run builds for new contributors, so a community manager will need to manually
kick off a build for a pull request from a new contributor.

The reason for this distinction is a matter of trust. Running a build means that
Jenkins will execute all the code in the pull request. A pull request can
contain any code whatsoever: if we allowed Jenkins to automatically build every
pull request, then a malicious developer could make our Jenkins server do whatever
he or she wanted. Before kicking off a build, community managers look at the
code changes to verify that they are not malicious; this protects us from nasty
people.

Once a contributor has submitted a few pull requests, they can request to be
added to the Jenkins whitelist: this is a special list of people that Jenkins
*will* kick off builds for automatically. If the community managers feel that
the contributor is trustworthy, then they will grant the request, which will
make future development faster and easier for both the contributor and edX. If
a contibutor shows that they can not be trusted for some reason, they will be
removed from this whitelist.

Failed Builds
=============

Click on the build to be brought to the build page. You'll see a matrix of blue
and red dots; the red dots indicate what section failing tests were present in.
You can click on the test name to be brought to an error trace that explains
why the tests fail. Please address the failing tests before requesting a new
build on your branch. If the failures appear to not have anything to do with
your code, it may be the case that the master branch is failing. You can ask
your reviewers for advice in this scenario.

If the build says "Unstable" but passes all tests, you have introduced too many
pep8 and pylint violations. Please refer to the documentation for :doc:`code-quality`
and clean up the code.

Successful Builds
=================

If all the tests pass, the "Diff Coverage" and "Diff Quality" reports are
generated. Click on the "View Reports" link on your pull request to be brought
to the Jenkins report page. In a column on the left side of the page are a few
links, including "Diff Coverage Report" and "Diff Quality Report". View each of
these reports (making note that the Diff Quality report has two tabs - one for
pep8, and one for Pylint).

Make sure your quality coverage is 100% and your test coverage is at least 95%.
Adjust your code appropriately if these metrics are not high enough. Be sure to
ask your reviewers for advice if you need it.


.. _Jenkins: http://jenkins-ci.org/
