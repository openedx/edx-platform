Feature: The help module should work
  In order to get help
  As a student
  I want to be able to report a problem


  Scenario: I can submit a problem when I am not logged in
    Given I visit the homepage
    When I click the help modal
    And I report a "problem"
    And I fill "name" with "Robot"
    And I fill "email" with "Robot@edx.org"
    And I fill "subject" with "Test Issue"
    And I fill "details" with "I am having a problem"
    And I submit the issue
    Then The submit button should be disabled

  Scenario: I can submit a problem when I am logged in
    Given I am registered for the course "6.002x"
    And I am logged in
    And I click on View Courseware
    When I click the help modal
    And I report a "problem"
    And I fill "subject" with "Test Issue"
    And I fill "details" with "I am having a problem"
    And I submit the issue
    Then The submit button should be disabled

