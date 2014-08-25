***********
Contributor
***********

Before you make a pull request, it’s a good idea to reach out to the edX
developers and the rest of the Open edX community to discuss your ideas. There
might well be someone else already working on the same change you want to make,
and it’s much better to collaborate than to submit incompatible pull requests.
You can `send an email to the mailing list`_, `chat on the IRC channel`_, or
`open an issue in our JIRA issue tracker`_. The earlier you start the
conversation, the easier it will be to make sure that everyone’s on the right
track -- before you spend a lot of time and effort making a pull request.

.. _send an email to the mailing list: https://groups.google.com/forum/#!forum/edx-code
.. _chat on the IRC channel: http://webchat.freenode.net?channels=edx-code
.. _open an issue in our JIRA issue tracker: https://openedx.atlassian.net

It’s also sometimes useful to submit a pull request even before the code is
working properly, to make it easier to collect early feedback. To indicate to
others that your pull request is not yet in a functional state, just prefix the
pull request title with "(WIP)" (which stands for Work In Progress).

Once you’re ready to submit your changes in a pull request, check the following
list of requirements to be sure that your pull request is ready to be reviewed:

#. The code should be clear and understandable.
   Comments in code, detailed docstrings, and good variable naming conventions
   are expected.

#. The pull request should be as small as possible.
   Each pull request should encompass only one idea: one bugfix, one feature,
   etc. Multiple features (or multiple bugfixes) should not be bundled into
   one pull request. A handful of small pull requests is much better than
   one large pull request.

#. Structure your pull request into logical commits.
   "Fixup" commits should be squashed together. The best pull requests contain
   only a single, logical change -- which means only a single, logical commit.

#. All code in the pull request must be compatible with edX’s AGPL license.
   This means that the author of the pull request must sign a `contributor's
   agreement with edX`_, and all libraries included or referenced in
   the pull request must have `compatible licenses`_.

#. All of the tests must pass.
   If a pull request contains a new feature, it should also contain
   new tests for that feature. If the pull request fixes a bug, it should
   also contain a test for that bug to be sure that it stays fixed.
   (edX’s continuous integration server will verify this for your pull request,
   and point out any failing tests.)

#. The author of the pull request should provide a test plan for verifying
   the change in this pull request. The test plan should include details
   of what should be checked, how to check it, and what the correct behavior
   should be.

#. For pull requests that make changes to the user interface,
   it’s very helpful if you can include screenshots of what you changed.
   In the future, the core committers will produce a style guide that
   contains more requirements around how pages should appear and how
   front-end code should be structured.

#. The pull request should contain some documentation for the feature or bugfix,
   either in a README file or in a comment on the pull request.
   A well-written description for the pull request may be sufficient.

#. The pull request should integrate with existing infrastructure as much
   as possible, rather than reinventing the wheel.  In a project as large as
   Open edX, there are many foundational components that might be hard to find,
   but it is important not to duplicate functionality, even if small,
   that already exists.

#. The author of the pull request should be receptive to feedback and
   constructive criticism.
   The pull request will not be accepted until all feedback from reviewers
   is addressed. Once a core committer has reviewed a pull request from a
   contributor, no further review is required from the core committer until
   the contributor has addressed all of the core committer’s feedback:
   either making changes to the pull request, or adding another comment
   explaining why the contributor has chosen not make any change
   based on that feedback.

It’s also important to realize that you and the core committers may have
different ideas of what is important in the codebase. The power and freedom of
open source software comes from the fact that you can fork our software and make
any modifications that you like, without permission from us; however, the core
committers are similarly empowered and free to decide what modifications to pull
in from other contributors, and what not to pull in. While your code might work
great for you on a small installation, it might not work as well on a large
installation, have problems with performance or security, not be compatible with
internationalization or accessibility guidelines, and so on. There are many,
many reasons why the core committers may decide not to accept your pull request,
even for reasons that are unrelated to the quality of your code change. However,
if we do reject your pull request, we will explain why we aren’t taking it, and
try to suggest other ways that you can accomplish the same result in a way that
we will accept.

Further Information
-------------------
For futher information on the pull request requirements, please see the following
links:

* :doc:`../code-considerations`
* :doc:`../testing/jenkins`
* :doc:`../testing/code-coverage`
* :doc:`../testing/code-quality`
* `Python Guidelines <https://github.com/edx/edx-platform/wiki/Python-Guidelines>`_
* `Javascript Guidelines <https://github.com/edx/edx-platform/wiki/Javascript-Guidelines>`_

.. _contributor's agreement with edX: http://code.edx.org/individual-contributor-agreement.pdf
.. _compatible licenses: https://github.com/edx/edx-platform/wiki/Licensing
