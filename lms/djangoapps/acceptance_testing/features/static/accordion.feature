Feature: Use the Accordion
  In order to access courseware
  As a registered student
  We'll attempt to access all the information

  Scenario: Click on every Week's Content
  Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
  When I click "LOG IN"
    And I login with "ddieker+admin@gmail.com" in the "email" field
    And I login with "password" in the "password" field
    And I press "Access My Courses"
    I should see an element with class of "user" within "3" seconds
  	I visit "http://stage-edx-001.m.edx.org/courses/BerkeleyX/CS188.1x/2012_Fall/info"
  	I click "Courseware"
  	I should see an element with id of "accordion"
  	I click on every item in every week of the course