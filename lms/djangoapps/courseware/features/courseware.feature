Feature: View the Courseware Tab
  As a student in an edX course
  In order to work on the course
  I want to view the info on the courseware tab

    Scenario: I can get to the courseware tab when logged in
    Given I am registered for a course
    And I log in
    And I click on View Courseware
    When I click on the "Courseware" tab
    Then the "Courseware" tab is active
