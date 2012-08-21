Feature: I can explore all the courses I am signed up for
  In order to learn from the courses I'm signed up for
  As a registered user with courses
  I want to be able to see all the chapters and all the section in each chapter 
    for each course

  Scenario: We can see all the courses
    Given I visit "http://localhost:8000/dashboard"
    I should see some courses
    