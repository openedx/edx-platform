Feature: Register for a course
  As a registered user
  In order to access my class content
  I want to register for a class on the edX website

  	Scenario: I can register for a course
  	Given I am logged in
    And I visit the courses page
		When I register for the course numbered "6.002x"
  	Then I should see the course numbered "6.002x" in my dashboard

    Scenario: I can unregister for a course
    Given I am logged in
    And I am registered for a course
    And I visit the dashboard
    When I click the link with the text "Unregister"
    And I press the "Unregister" button in the Unenroll dialog
    Then I should see "Looks like you haven't registered for any courses yet." somewhere in the page