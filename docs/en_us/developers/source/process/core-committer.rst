**************
Core Committer
**************

Core committers are responsible for doing code review on pull requests from
contributors, once the pull request has passed through a community manager and
been prioritized by a product owner. As much as possible, the code review
process should be treated identically to the process of reviewing a pull request
from another core committer: we’re all part of the same community. However,
there are a few ways that the process is different:

* The contributor cannot see when conflicts occur in the branch.
  These conflicts prevent the pull request from being merged,
  so you should ask the contributor to rebase their pull request,
  and point them to the documentation for doing so.

* Jenkins may not run on the contributor’s pull request automatically.
  Be sure to start new Jenkins jobs for the PR as necessary -- do not approve
  a pull request unless Jenkins has run, and passed, on the last commit
  in the pull request. If this contributor has already contributed a few
  good pull requests, that contributor can be added to the Jenkins whitelist,
  so that jobs are run automatically.

* The contributor may not respond to comments in a timely manner.
  This is not your concern: you can move on to other things while waiting.
  If there is no response after a few days, a community manager will warn the
  contributor that if the comments are not addressed, the pull request will
  be closed. (You can also warn the contributor yourself, if you wish.)
  Do not close the pull request merely because the contributor hasn’t responded
  -- if you think the pull request should be closed, inform the
  community managers, and they will handle it.

Each Scrum team should decide for themselves how to estimate stories related to
reviewing external pull requests, and how to claim points for those stories,
keeping in mind that an unresponsive contributor may block the story in ways
that the team can’t control. When deciding how many contributor pull request
reviews to commit to in the upcoming iteration, teams should plan to spend about
two hours per week per developer on the team -- larger teams can plan to spend
more time than smaller teams. This is just a guideline, however: the teams can
decide for themselves how many contributor pull request reviews they want to
commit to.

Once a pull request from a contributor passes all required code reviews, a core
committer will need to merge the pull request into the project. The core
committer who merges the pull request will be responsible for verifying those
changes on the staging server prior to release, using the test plan provided by
the author of the pull request.

In addition to reviewing contributor requests as part of sprint work, core
committers should expect to spend about one hour per week doing other tasks
related to the open source community: reading/responding to questions on the
mailing list and/or IRC channel, disseminating information about what edX is
working on, and so on.
