
#### What's this PR do? Any additional context?

#### Where should the reviewer start?

#### How can this be manually tested? (brief repro steps)

#### What are the relevant TFS items? (list id numbers)

#### Definition of done:
- [ ] Title of the pull request is clear and informative
- [ ] Add pull request hyperlink to relevant TFS items
- [x] For large or complex change: schedule an in-person review session

[//]: # ( todo: Is there appropriate test coverage? )
[//]: # ( todo: Does this PR require a new Selenium test? )
[//]: # ( todo: Is there appropriate logging/monitoring included? )

#### Reminders BEFORE merging
1. Get at least two approvals
1. If you're merging into the development branch then "flatten" or "squash" commits
1. If merging from development into master then don't "flatten" or "squash" commits

#### Reminders AFTER merging
1. Delete the remote branch
1. Resolve relevant TFS items
1. (reverse merge) If you merged into master then check to see if there are any changes in master that can be merged down to the development branch (like hotfixes, etc)

[//]: # ( todo: If you merged into development branch then verify change in our "rolling deployment" environment. Then notify stakeholders interested in or involved with the change )


[//]: # ( fyi: This content was heavily inspired by )
[//]: # ( 1 Our team's policies and processes )
[//]: # ( 3 https://github.com/sprintly/sprint.ly-culture/blob/master/pr-template.md )
[//]: # ( 4 The book "The Checklist Manifesto: How to Get Things Right" by Atul Gawande )
[//]: # ( 5 https://github.com/Azure/azure-event-hubs/blob/master/.github/PULL_REQUEST_TEMPLATE.md )
