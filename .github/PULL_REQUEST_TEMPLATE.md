
#### What does this PR do? Please provide some context

#### Where should the reviewer start?

#### How can this be manually tested? (brief repro steps)

#### What are the relevant TFS items? (list id numbers)

#### Definition of done:
- [ ] Title of the pull request is clear and informative
- [ ] Add pull request hyperlink to relevant TFS items
- [ ] For large or complex change: schedule an in-person review session
- [ ] This change has appropriate test coverage

#### Reminders BEFORE merging
1. Get at least two approvals
1. If you're merging from a feature branch into the development branch then "flatten" or "squash" commits
1. If merging from the development branch into master (or porting changes from upstream) then use github's UI to get review feedback, but use the git command line interface to complete the actual merge.

#### Reminders AFTER merging
1. Delete the remote feature branch
1. Resolve relevant TFS items
1. (reverse merge) If you merged from the development branch into master then check to see if there are any changes in master that can be merged down to the development branch (like hotfixes, etc). In this case, use github's UI for feedback and the git command line interface for the actual merge.

[//]: # ( todo: If you merged into development branch then verify change in our "rolling deployment" environment. Then notify stakeholders interested in or involved with the change )

[//]: # ( fyi: This content was heavily inspired by )
[//]: # ( 1 Our team's policies and processes )
[//]: # ( 2 https://github.com/sprintly/sprint.ly-culture/blob/master/pr-template.md )
[//]: # ( 3 The book "The Checklist Manifesto: How to Get Things Right" by Atul Gawande )
[//]: # ( 4 https://github.com/Azure/azure-event-hubs/blob/master/.github/PULL_REQUEST_TEMPLATE.md )
