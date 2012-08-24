Feature: There are many different types of tabs
  In order to validate tab types
  As a staff member
  I want to try out all the videos, buttons, and content

  Scenario: Login to an existing account
  Given I visit and check 502 for "http://www.edx.org/dashboard"
  When I click "LOG IN"
    And I login with "ddieker+admin@gmail.com" in the "email" field
    And I login with "password" in the "password" field
    And I press "Access My Courses"
  Then I should see an element with class of "user" within "3" seconds

  Scenario: I visit a tabbed quiz
  Given I visit and check 502 for "http://www.edx.org/courses/MITx/6.002x-EE98/2012_Fall_SJSU/courseware/Week_0/Administrivia_and_Circuit_Elements/"
    I process