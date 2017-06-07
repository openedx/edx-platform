Security Release Pull Request
---

For details on the edx.org security release process, see here:

[LMS/Studio Security Release Process](https://openedx.atlassian.net/wiki/pages/viewpage.action?pageId=158318452)

Before creating a pull request in this repo:

  - [ ] Ensure that you've read the [LMS/Studio Security Release Process](https://openedx.atlassian.net/wiki/pages/viewpage.action?pageId=158318452) and you understand the process.
  - [ ] Inform a DevOps team member that you're creating a security patch.

While creating your pull request:

  - [ ] Use the correct base for your pull request, currently `security-release`.

After creating your pull request:

  - [ ] **DO NOT MERGE THE PULL REQUEST!**
    - Until you're ready for the PR to go public, it should *NOT* be merged.
  - [ ] Request PR reviews from appropriate developers and at least one DevOps team member.
    - The reviewers should "Approve" the PR - but should *NOT* merge the PR.

**ONLY** when you're ready for the change to go public:

  - [ ] Merge the pull request.
    - An automated process will merge the change back to the paired public repository.
