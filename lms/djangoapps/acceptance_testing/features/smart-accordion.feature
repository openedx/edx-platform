Feature: There are courses on the homepage
  In order to compared rendered content to the database
  As an acceptance test
  I want to count all the chapters, sections, and tabs for each course

  Scenario: We can see all the courses
    Given I visit "http://localhost:8000/"
    I verify all the content of each course