@shard_2
Feature: LMS.Annotatable Component
  As a student, I want to view an Annotatable component in the LMS

  Scenario: An Annotatable component can be rendered in the LMS
    Given that a course has an annotatable component with 2 annotations
    When I view the annotatable component
    Then the annotatable component has rendered
    And the annotatable component has 2 highlighted passages

# Disabling due to frequent intermittent failures. TNL-353
# This features's acceptance tests should be rewritten in bok-choy, rather than fixed here.
#
#  Scenario: An Annotatable component links to annonation problems in the LMS
#    Given that a course has an annotatable component with 2 annotations
#    And the course has 2 annotatation problems
#    When I view the annotatable component
#    And I click "Reply to annotation" on passage <problem>
#    Then I am scrolled to that annotation problem
#    When I answer that annotation problem
#    Then I receive feedback on that annotation problem
#    When I click "Return to annotation" on that problem
#    Then I am scrolled to the annotatable component
#
#    Examples:
#    | problem |
#    | 0       |
#    | 1       |
