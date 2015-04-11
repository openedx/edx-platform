############################
Contributing to Open edX
############################

Contributions to Open edX are very welcome, and strongly encouraged! We've
put together `some documentation that describes our contribution process`_,
but here's a step-by-step guide that should help you get started.

.. _some documentation that describes our contribution process: http://edx.readthedocs.org/projects/userdocs/en/latest/process/overview.html

Step 0: Join the Conversation
=============================

Got an idea for how to improve the codebase? Fantastic, we'd love to hear about
it! Before you dive in and spend a lot of time and effort making a pull request,
it's a good idea to discuss your idea with other interested developers and/or the
edX product team. You may get some valuable feedback that changes how you think
about your idea, or you may find other developers who have the same idea and want
to work together.

If you've got an idea for a new feature or new functionality for an existing feature,
please start a discussion on the `edx-code`_ mailing list to get feedback from
the community about the idea and your implementation choices.

.. _edx-code: https://groups.google.com/forum/#!forum/edx-code

If you then plan to contribute your code upstream, please `start a discussion on JIRA`_
(you may first need to `create a free JIRA account`_).
Start a discussion by visiting the JIRA website and clicking the "Create" button at the
top of the page. Choose the project "Open Source Pull Requests" and the issue type
"Feature Proposal". In the description give us as much detail as you can for the feature
or functionality you are thinking about implementing. Include a link to any relevant
edx-code mailing list discussions about your idea. We encourage you to do this before
you begin implementing your feature, in order to get valuable feedback from the edX
product team early on in your journey and increase the likelihood of a successful
pull request.

.. _start a discussion on JIRA: https://openedx.atlassian.net/secure/Dashboard.jspa
.. _create a free JIRA account: https://openedx.atlassian.net/admin/users/sign-up

For real-time conversation, we use `IRC`_: we all hang out in the
`#edx-code channel on Freenode`_. Come join us! The channel tends to be most
active Monday through Friday between 13:00 and 21:00 UTC
(9am to 5pm US Eastern time), but interesting conversations can happen
at any time.

.. _IRC: http://www.irchelp.org/
.. _#edx-code channel on Freenode: http://webchat.freenode.net/?channels=edx-code

For asynchronous conversation, we have several mailing lists on Google Groups:

* `openedx-ops`_: everything related to *running* Open edX. This includes
  installation issues, server management, cost analysis, and so on.
* `openedx-translation`_: everything related to *translating* Open edX into
  other languages. This includes volunteer translators, our internationalization
  infrastructure, issues related to Transifex, and so on.
* `openedx-analytics`_: everything related to *analytics* in Open edX.
* `edx-code`_: everything related to the *code* in Open edX. This includes
  feature requests, idea proposals, refactorings, and so on.

.. _openedx-ops: https://groups.google.com/forum/#!forum/openedx-ops
.. _openedx-translation: https://groups.google.com/forum/#!forum/openedx-translation
.. _openedx-analytics: https://groups.google.com/forum/#!forum/openedx-analytics
.. _edx-code: https://groups.google.com/forum/#!forum/edx-code

Byte-sized Tasks & Bugs
-----------------------

If you are contributing for the first time and want a gentle introduction,
or if you aren't sure what to work on, have a look at the list of
`byte-sized bugs and tasks`_ in the tracker. These tasks are selected for their
small size, and usually don't require a broad knowledge of the edX platform.
It makes them good candidates for a first task, allowing you to focus on getting
familiar with the development environment and the contribution process.

.. _byte-sized bugs and tasks: http://bit.ly/edxbugs

Once you have identified a bug or task, `create an account on the tracker`_ and
then comment on the ticket to indicate that you are working on it. Don't hesitate
to ask clarifying questions on the ticket as needed, too, if anything is unclear.

.. _create an account on the tracker: https://openedx.atlassian.net/admin/users/sign-up

Step 1: Sign a Contribution Agreement
=====================================

Before edX can accept any code contributions from you, you'll need to sign
the `individual contributor agreement`_ and send it in. This confirms
that you have the authority to contribute the code in the pull request and
ensures that edX can relicense it.

You should print out the agreement and sign it. Then scan (or photograph) the
signed agreement and email it to the email address indicated on the agreement.
Alternatively, you're also free to physically mail the agreement to the street
address on the agreement. Once we have your agreement in hand, we can begin
reviewing and merging your work.

You'll also need to add yourself to the `AUTHORS` file when you submit your
first pull request.  You should add your full name as well as the email address
associated with your GitHub account.  Please update `AUTHORS` in an individual
commit, distinct from other changes in the pull request (it's OK for a pull
request to contain multiple commits, including a commit to `AUTHORS`).
Alternatively, you can open up a separate PR just to have your name added to
the `AUTHORS` file, and link that PR to the PR with your changes.

Step 2: Fork, Commit, and Pull Request
======================================
GitHub has some great documentation on `how to fork a git repository`_. Once
you've done that, make your changes and `send us a pull request`_! Be sure to
include a detailed description for your pull request, so that a community
manager can understand *what* change you're making, *why* you're making it, *how*
it should work now, and how you can *test* that it's working correctly.

.. _how to fork a git repository: https://help.github.com/articles/fork-a-repo
.. _send us a pull request: https://help.github.com/articles/creating-a-pull-request

Step 3: Meet PR Requirements
============================

Our `contributor documentation`_ includes a long list of requirements that pull
requests must meet in order to be reviewed by a core committer. These requirements
include things like documentation and passing tests: see the
`contributor documentation`_ page for the full list.

.. _contributor documentation: http://edx.readthedocs.org/projects/userdocs/en/latest/process/contributor.html

Step 4: Approval by Community Manager and Product Owner
=======================================================

A community manager will read the description of your pull request. If the
description is understandable, the community manager will send the pull request
to a product owner. The product owner will evaluate if the pull request is a
good idea for Open edX, and if not, your pull request will be rejected. This
is another good reason why you should discuss your ideas with other members
of the community before working on a pull request!

Step 5: Code Review by Core Committer(s)
========================================

If your pull request meets the requirements listed in the
`contributor documentation`_, and it hasn't been rejected by a product owner,
then it will be scheduled for code review by one or more core committers. This
process sometimes takes awhile: most of the core committers on the project
are employees of edX, and they have to balance their time between code review
and new development.

Once the code review process has started, please be responsive to comments on
the pull request, so we can keep the review process moving forward.
If you are unable to respond for a few days, that's fine, but
please add a comment informing us of that -- otherwise, it looks like you're
abandoning your work!

Step 6: Merge!
==============

Once the core committers are satisfied that your pull request is ready to go,
one of them will merge it for you. Your code will end up on the edX production
servers in the next release, which usually which happens every week. Congrats!


############################
Expectations We Have of You
############################

By opening up a pull request, we expect the following things:

1. You've read and understand the instructions in this contributing file and
   the contribution process documentation.

2. You are ready to engage with the edX community. Engaging means you will be
   prompt in following up with review comments and critiques. Do not open up a
   pull request right before a vacation or heavy workload that will render you
   unable to participate in the review process.

3. If you have questions, you will ask them by either commenting on the pull
   request or asking us in IRC or on the mailing list.

4. If you do not respond to comments on your pull request within 7 days, we
   will close it. You are welcome to re-open it when you are ready to engage.

############################
Expectations You Have of Us
############################

1. Within a week of opening up a pull request, one of our community managers
   will triage it, starting the documented contribution process. (Please
   give us a little extra time if you open the PR on a weekend or
   around a US holiday! We may take a little longer getting to it.)

2. We promise to engage in an active dialogue with you from the time we begin
   reviewing until either the PR is merged (by a core committer), or we
   decide that, for whatever reason, it should be closed.

3. Once we have determined through visual review that your code is not
   malicious, we will run a Jenkins build on your branch.

.. _individual contributor agreement: http://open.edx.org/sites/default/files/wysiwyg/individual-contributor-agreement.pdf
