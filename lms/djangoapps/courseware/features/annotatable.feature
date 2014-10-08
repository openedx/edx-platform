@shard_2
Feature: LMS.Annotatable Component
  As a student, I want to view an Annotatable component in the LMS

  Scenario: An Annotatable component can be rendered in the LMS
    Given that a course has an annotatable component with 2 annotations
    When I view the annotatable component
    Then the annotatable component has rendered
    And the annotatable component has 2 highlighted passages
