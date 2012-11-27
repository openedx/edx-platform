Feature: There are many different types of tabs
  In order to validate tab types
  As a staff member
  I want to try out all the videos, buttons, and content

  Scenario: I visit a tabbed quiz
    Given I am registered for course "MITx/6.002x-EE98/2012_Fall_SJSU"
    And I log in
    Given I visit and check 502 for "http://www.edx.org/courses/MITx/6.002x-EE98/2012_Fall_SJSU/courseware/Week_0/Administrivia_and_Circuit_Elements/"
    I process
