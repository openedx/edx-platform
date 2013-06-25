Feature: Course Settings
  As a course author, I want to be able to configure my course settings.

  Scenario: User can set course dates
    Given I have opened a new course in Studio
    When I select Schedule and Details
    And I set course dates
    And I save my changes
    Then I see the set dates on refresh

  Scenario: User can clear previously set course dates (except start date)
    Given I have set course dates
    And I clear all the dates except start
    And I save my changes
    Then I see cleared dates on refresh

  Scenario: User cannot clear the course start date
    Given I have set course dates
    And I save my changes
    And I clear the course start date
    Then I receive a warning about course start date
    And The previously set start date is shown on refresh

  Scenario: User can correct the course start date warning
    Given I have tried to clear the course start
    And I have entered a new course start date
    And I save my changes
    Then The warning about course start date goes away
    And My new course start date is shown on refresh

  Scenario: Settings are only persisted when saved
    Given I have set course dates
    And I save my changes
    When I change fields
    And I cancel my changes
    Then I do not see the new changes persisted on refresh
