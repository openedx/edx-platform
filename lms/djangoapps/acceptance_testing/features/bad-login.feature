Feature: There are courses on the homepage
  In order to compared rendered content to the database
  As an acceptance test
  I want to count all the chapters, sections, and tabs for each course

  Scenario: Login to an existing account
  Given I visit "http://localhost:8000/"
  When I click "LOG IN"
    And I login with "ddieker++@gmail.com" in the "email" field
    And I login with "password" in the "password" field
    And I press "Access My Courses"
  Then I should see an element with class of "user" within "3" seconds
