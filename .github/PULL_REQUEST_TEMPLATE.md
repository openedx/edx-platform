### Please consider the following when opening a pull request:

- Link to the relevant JIRA ticket(s) and tag any relevant team(s).
- Squash your changes down into one or more discrete commits.
  In each commit, include description that could help a developer
  several months from now.
- If running `make upgrade`, run _as close to the time of merging as possible_
  to avoid accidentally downgrading someone else's package.
  Put the output of `make upgrade` in its own separate commit,
  decoupled from other code changes.
- Aim for comprehensive test coverage, but remember that
  automated testing isn't a substitute for manual verification.
- Carefully consider naming, code organization, dependencies when adding new code.
  Code that is amenable to refactoring and improvement benefits all platform developers,
  especially given the size and scope of edx-platform.
  Consult existing Architectural Decision Records (ADRs),
  including those concerning the app(s) you are changing and
  [those concerning edx-platform as a whole](https://github.com/edx/edx-platform/tree/master/docs/decisions).
