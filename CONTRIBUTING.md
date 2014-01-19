Contributing to edx-platform
============================

Contributions to edx-platform are very welcome, and strongly encouraged! The
easiest way is to fork the repo and then make a pull request from your fork.
Read on for details on how to become a contributor, edx-platform code quality,
testing, making a pull request, and more.


Becoming a Contributor
---
Before your first pull request is merged, you'll need to sign the
[individual contributor agreement](http://code.edx.org/individual-contributor-agreement.pdf)
and send it in. This confirms you have the authority to contribute the code in
the pull request and ensures we can relicense it.

You should print out the agreement and sign it. Then scan (or photograph) the signed agreement
and email it to the email address indicated on the agreement. Alternatively, you're also free
to physically mail the agreement to the street address on the agreement. Once we have your
agreement in hand, we can begin merging your work.

You'll also need to add yourself to the `AUTHORS` file when you submit your first pull request.
You should add your full name as well as the email address associated with your Github account.
Please update `AUTHORS` in an individual commit, distinct from other changes in the pull request (it's OK for a pull request to contain multiple commits, including a commit to `AUTHORS`). Alternatively, you can open up a separate PR just to have your name added to the `AUTHORS` file, and link that PR to the PR with your changes.


Code Quality Guidelines
---
###Comments

We expect you to contribute code that is self-documenting as much as possible. This means
submitting code with well-formed variable, function, class, and method names; good docstrings;
lots of comments. Use your discretion - not every line needs to be commented. However, code
that is obtuse is hard to maintain and hard for others to build upon. So please do your best
to provide code that is easy to read and well-commented.

###Python/Javascript Styling

Before you submit your first pull request, please review the edx-platform code quality
and style guidelines:

* [Python Guidelines](https://github.com/edx/edx-platform/wiki/Python-Guidelines)
* [Javascript Guidelines](https://github.com/edx/edx-platform/wiki/Javascript-Guidelines)

Coding conventions should be followed. Your submission should not introduce any new
pep8 or pylint errors (and ideally, should fix up other errors you encounter in the
files you edit). From the edx-platform main directory, you can run the command

`$ rake quality`

to print the "Diff Quality" report, a report of the quality violations your branch has made.

Although we try to be vigilant and resolve all quality violations, some Pylint violations
are just too challenging to resolve, so we opt to ignore them via use of a
pragma. A pragma tells Pylint to ignore the violation in the given line. An example is:

`self.assertEquals(msg, form._errors['course_id'][0])  # pylint: disable=protected-access`

The pragma starts with a `#` two spaces after the end of the line. We prefer that you use
the full name of the error (`pylint: disable=unused-argument` as opposed to
`pylint: disable=W0613`), so it's more clear what you're disabling in the line.

If you have any questions, don't hesitate to reach out to us on email or IRC; see 
the section on **Contacting Us**, below, for more.


Testing Coverage Guidelines
---

Before you submit a pull request, please refer to the [edx-platform testing documentation](https://github.com/edx/edx-platform/blob/master/docs/internal/testing.md).

Code you commit should *increase* test coverage, not decrease it. For more involved
contributions, you may want to discuss your intentions on the mailing list *before* you
start coding.

Running the command

`$ rake test`

in the edx-platform directory will run all the unit tests on edx-platform (to run specific
tests, refer to the testing documentation). Once you've run this command, you can run

`$ rake coverage`

to generate the "Diff Coverage" report. This report tells you how much of the Python and
JavaScript code you've changed is covered by unit tests. We aim for a coverage report score of
95% or higher. We also encourage you to write acceptance tests as your changes require. For
more in-depth help on various types of tests, please refer to the [edx-platform testing documentation](https://github.com/edx/edx-platform/blob/master/docs/internal/testing.md).



Opening Up A Pull Request
---

When you open up a pull request, please follow these guidelines:

* In the PR description, please be as clear as possible explaining what the change is. This helps us so much in contextualizing your PR and providing appropriate reviewers for you. Take a look at [#1322](https://github.com/edx/edx-platform/pull/1322) for an example of a verbose PR description for a new feature.

* As far as code goes, a first pass is to make sure that your code is of high quality. This means ensuring plenty of comments, as well as a 100% pass rate when you run `rake quality` locally. See the section **Code Quality Guidelines**.

* Testing coverage should be as complete as possible. 95% or greater on JavaScript and Python coverage (you can check this by running `rake test; rake coverage` locally). Percentage coverage is only calculated from unit tests, however. If you're adding new visual features, we love seeing acceptance tests as applicable. See the section **Testing Coverage Guidelines**.

* Be sure that your commit history is *clean* - that is, you don't have a ton of tiny commits with throwaway commit messages such as "Fix", "Arugh", "asdfjkl;", "Merge branch Master into fork", etc. Commit messages should be concise and explain what work was done. The first line should be fewer than 50 characters; you may add additional lines to your commit messages for further explaination.
	* To clean up your commit history you'll need to perform an *interactive rebase* where you squash your commits together. More about interactive rebase can be found in the [github help documents](https://help.github.com/articles/interactive-rebase) or by Googling.
	* The reasoning behind a clean commit history is that we want the log of all commits in edx-platform to be readable and self-documenting. This way, developers can take a look at all recent commits in the past few days or weeks and have a good understanding of all the code changes that were made.

* The `CHANGELOG` is a list of changes to the platform, distinct from the git log because the audience is not developers but rather users of our platform (specifically, course authors). Please make an entry in `CHANGELOG` describing your change if it is something that you think platform users would be interested in - eg a major bugfix, new feature, or update to existing functionality. Be sure to also indicate what system (LMS, CMS, etc) your change affects. If in doubt if your change is "big enough", we encourage you to make a `CHANGELOG` entry!

* Make sure that your branch is freshly rebased on master when you go to open your pull request. If you don't have repo permissions, you won't be able to see if your branch is able to be cleanly merged or not. We'll tell you if it's not; however, rebasing before you open your PR will help decrease the frequency of conflicts.

	* If you need help with rebasing, please see the following resources:
	1. [Git Book](http://git-scm.com/book/en/Git-Branching-Rebasing)
	2. [Git Docs](http://git-scm.com/docs/git-rebase)
	3. [Interactive Git tutorial](http://pcottle.github.io/learnGitBranching/) -- totally awesome!!
	4. [Git Ready](http://gitready.com/intermediate/2009/01/31/intro-to-rebase.html)


Finally, **Please Do Not** close a pull request and open a new one to respond to review
comments. Keep the same pull request open, so it's clear how your code has been worked upon
and what reviewers have been involved in the conversation. Rebase as needed to get updated
code from master into your branch.

### Expectations We Have of You

By opening up a pull request, we expect the following things:

1. You've read and understand the instructions in this contributing file.
2. You are ready to engage with the edX community. Engaging means you will be prompt in following up with review comments and critiques. Do not open up a pull request right before a vacation or heavy workload that will render you unable to participate in the review process.
3. If you have questions, you will ask them by either commenting on the pull request or asking us in IRC or on the mailing list. 
4. If you do not respond to comments on your pull request within 7 days, we will close it. You are welcome to re-open it when you are ready to engage.

### Expections You Have of Us

1. Within a week of opening up a pull request, one of our open source community managers will triage it, either tagging other reviewers for the PR or asking follow up questions (Please give us a little extra time if you open the PR on a weekend or around a US holiday! We may take a little longer getting to it.).
2. We promise to engage in an active dialogue with you from the time we begin reviewing until either the PR is merged (by an edX staff member), or we decide that, for whatever reason, it should be closed.
3. Once we have determined through visual review that your code is not malicious, we will run a Jenkins build on your branch.


### Using Jenkins Builds

When you open up a pull request, an edX staff member can decide to run a Jenkins build on your
branch. We will do this once we have determined that your code is not malicious.

When a Jenkins job is run, all unit, javascript, and acceptance tests are run.

**If the build fails...**

Click on the build to be brought to the build page. You'll see a matrix of blue and red dots;
the red dots indicate what section failing tests were present in. You can click on the test
name to be brought to an error trace that explains why the tests fail. Please address the
failing tests before requesting a new build on your branch. If the failures appear to not have
anything to do with your code, it may be the case that the master branch is failing. You can
ask your reviewers for advice in this scenario.

If the build says "Unstable" but passes all tests, you have introduced too many pep8 and pylint
violations. Please refer to the **Code Quality Guidelines** section and clean up the code.

**If the build passes...**

If all the tests pass, the "Diff Coverage" and "Diff Quality" reports are generated. Click on
the "View Reports" link on your pull request to be brought to the Jenkins report page. In a
column on the left side of the page are a few links, including "Diff Coverage Report" and "Diff
Quality Report". View each of these reports (making note that the Diff Quality report has two
tabs - one for pep8, and one for Pylint). 

Make sure your quality coverage is 100% and your test coverage is at least 95%. Adjust your
code appropriately if these metrics are not high enough. Be sure to ask your reviewers for advice if you need it.



Contacting Us
---

### Mailing list

If you have any questions, please ask on the
[mailing list](https://groups.google.com/forum/#!forum/edx-code). It's always a good idea to
first search through the archives, to see if any of your questions have already been asked and
answered.

The edx platform team is based in the US, so we're best able to respond to questions posted in
English. You're most likely to get an answer if you ask questions related to edx-platform code
or conventions. Questions only tangentially related to edx-platform may be better answered on
different forums or mailing lists (for example, asking for help on how to set up Git is better
posted on a Git related message list or forum).

Questions about translations, XBlock, creating courses, or using Studio are not appropriate for
the edx-code mailing list. We have a few other mailing lists you may be interested in:
* [openedx-translation](https://groups.google.com/forum/#!forum/openedx-translation)
* [edx-xblock](https://groups.google.com/forum/#!forum/edx-xblock)
* [openedx-studio](https://groups.google.com/forum/#!forum/openedx-studio)

### IRC

Many edX employees and community members hang out in the #edx-code [IRC channel](http://www.irchelp.org/irchelp/new2irc.html) on Freenode.
We're always happy to see more people hanging out with us there!

**Tips on Using IRC**

For clients, the [webchat](webchat.freenode.net) is easiest, because you don't need to install anything and it's cross-platform. [ChatZilla](http://chatzilla.hacksrus.com/) is almost as easy -- it's a Firefox extension, and works anywhere Firefox does. For an installed application, [Pidgin](http://pidgin.im) works decently (or [Adium](https://adium.im) on Mac), and has a familiar instant-messenger-style interface. For something truly dedicated to IRC, there's [mIRC](http://www.mirc.com) for Windows (free), [LimeChat](http://limechat.net/mac/) for Mac (free), or [Textual](http://www.codeux.com/textual/) for Mac (paid). There are also many other clients out there, but those are some good recommendations for people relatively new to IRC.

### Pull requests/issues

We do not make much use of github issues, so opening an issue on edx-platform is not the
best way to reach us. However, when you've opened up a pull request, please please don't
be shy about adding comments and having a robust conversation with your pull request reviewers.

Your pull request is a good place to ask pointed questions about the code you've written, and
we're very happy to have interaction with you through code, commits, and comments.