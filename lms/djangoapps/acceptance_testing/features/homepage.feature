Feature: There are courses on the homepage
  In order to view and sign up for courses
  As anonymous web users
  We want to be able to see all the courses available on the home page

  Scenario: We can see all the courses
    Given I visit "http://localhost:8000/"
    I should see all courses