Feature: View the Course Info tab
  As a student in an edX course
  In order to get background on the course
  I want to view the info on the course info tab

    Scenario: I can get to the course info tab when logged in
    Given I am logged in
    And I am registered for a course
    And I visit the dashboard    
    When I click on View Courseware
    Then I am on an info page
    And the Course Info tab is active
    And I do not see "! Info section missing !" anywhere on the page

    # This test is currently failing
    # see: https://www.pivotaltracker.com/projects/614553?classic=true#!/stories/38801223
    Scenario: I cannot get to the course info tab when not logged in
    Given I am not logged in
    And I visit the homepage
    When I visit the course info URL    
    Then the login dialog is visible