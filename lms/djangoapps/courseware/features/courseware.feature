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

    # TODO: fix this one? Not sure whether you should get a 404.
    # Scenario: I cannot get to the courseware tab when not logged in
    # Given I am not logged in
    # And I visit the homepage
    # When I visit the courseware URL    
    # Then the login dialog is visible