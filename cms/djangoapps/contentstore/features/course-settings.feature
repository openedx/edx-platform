Feature: Course Settings
  As a course author, I want to be able to configure my course settings.

  Scenario: User can set course dates
    Given I have opened a new course in Studio
    When I select Schedule and Details
    And I set course dates
    Then I see the set dates on refresh

  Scenario: User can clear previously set course dates (except start date)
    Given I have set course dates
    And I clear all the dates except start
    Then I see cleared dates on refresh

  Scenario: User cannot clear the course start date
    Given I have set course dates
    And I clear the course start date
    Then I receive a warning about course start date
    And The previously set start date is shown on refresh

  Scenario: User can correct the course start date warning
    Given I have tried to clear the course start
    And I have entered a new course start date
    Then The warning about course start date goes away
    And My new course start date is shown on refresh
