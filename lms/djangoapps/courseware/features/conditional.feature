# Disabled by labster, converted to bok-choy in
# https://github.com/edx/edx-platform/commit/07573c51417ac5d962aac3590da39cc5152c68f0
# @shard_2
# Feature: LMS.Conditional Module
#   As a student, I want to view a Conditional component in the LMS

#   Scenario: A Conditional hides content when conditions aren't satisfied
#     Given that a course has a Conditional conditioned on problem attempted=True
#     And that the conditioned problem has not been attempted
#     When I view the conditional
#     Then the conditional contents are hidden

#   Scenario: A Conditional shows content when conditions are satisfied
#     Given that a course has a Conditional conditioned on problem attempted=True
#     And that the conditioned problem has been attempted
#     When I view the conditional
#     Then the conditional contents are visible

#   Scenario: A Conditional containing a Poll is updated when the poll is answered
#     Given that a course has a Conditional conditioned on poll poll_answer=yes
#     When I view the conditional
#     Then the conditional contents are hidden
#     When I answer the conditioned poll "yes"
#     Then the conditional contents are visible
