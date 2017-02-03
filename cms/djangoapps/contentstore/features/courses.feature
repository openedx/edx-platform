@shard_2
Feature: CMS.Create Course
  In order offer a course on the edX platform
  As a course author
  I want to create courses

  Scenario: Error message when org/course/run tuple is too long
    Given There are no courses
    And I am logged into Studio
    When I click the New Course button
    And I create a course with "course name", "012345678901234567890123456789", "012345678901234567890123456789", and "0123456"
    Then I see an error about the length of the org/course/run tuple
    And the "Create" button is disabled

  Scenario: Course name is not included in the "too long" computation
    Given There are no courses
    And I am logged into Studio
    When I click the New Course button
    And I create a course with "012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789", "org", "coursenum", and "run"
    And I press the "Create" button
    Then the Courseware page has loaded in Studio
