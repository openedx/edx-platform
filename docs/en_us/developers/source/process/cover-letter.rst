*************************
Pull Request Cover Letter
*************************

When opening up a pull request, please prepare a "cover letter" to place into
the "Description" field on Github. A good cover letter concisely answers as
many of the following questions as possible. Not all pull requests will have
answers to every one of these questions, which is okay!

* What JIRA ticket does this address? Please provide a link to the JIRA ticket
  representing the bug you are fixing or the feature discussion you've already
  had with the edX product owners.

* Who have you talked to at edX about this work? Design, architecture, previous PRs,
  course project manager, IRC, mailing list, etc.

* What components are affected? (LMS, Studio, a specific app in the system, etc)

* What users are affected?  For example, is this a new component intended for use
  in just one course, or is this a system wide change affecting all edX students?

* Test instructions for manual testing. When it makes sense to do so, a good test
  plan includes a tarball of a small test course that has a unit which triggers
  the bug or illustrates the new feature. Another option would be to provide
  explicit, numbered steps (potentially with screenshots!) to walk the reviewer
  through your feature or fix.

* Please provide screenshots for all user-facing changes

* Indicate the urgency of your request. If this is a pull request for a course
  running or about to run on edx.org, we need to understand your time constraints.
  Good pieces of information to provide are the course(s) that need this feature
  and the date that the feature needed by.

* What are your concerns (the author’s) about the PR? Is there a corner case you
  don't know how to address or some tests you aren't sure how to add? Please bring
  these concerns up in your cover letter so we can help!


Example Of A Good PR Cover Letter
---------------------------------

`Pull Request 4675`_ is one of the first edX pull requests to include a cover
letter, and it is great! It clearly explains what the bug is, what system is
affected (just the LMS), includes a tarball of a course that demonstrates the
issue, and provides clear manual testing instructions.

`Pull Request 4983`_ is another great example. This pull request's cover letter
includes before and after screenshots, so the UX team can quickly understand
what changes were made and make suggestions. Further, the pull request indicates
how to manually test the feature and what date it is needed by.

.. _Pull Request 4675: https://github.com/edx/edx-platform/pull/4675
.. _Pull Request 4983: https://github.com/edx/edx-platform/pull/4983
