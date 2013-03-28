Feature: Create Course
  In order offer a course on the edX platform
  As a course author
  I want to create courses

  Scenario: Create a course
    Given There are no courses
    And I am logged into Studio
    When I click the New Course button
    And I fill in the new course information
    And I press the "Save" button
    Then the Courseware page has loaded in Studio
    And I see a link for adding a new section
