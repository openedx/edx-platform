Feature: All the high level tabs should work
  In order to make sure high level tabs work
  As an acceptance test
  I want to click Courseware, Course Info, Discussion, Wiki, Progress, Instructor

  Scenario: Login to an existing staff account
  Given I visit "http://www.edx.org"
  When I click "LOG IN"
    And I login with "ddieker+admin@gmail.com" in the "email" field
    And I login with "password" in the "password" field
    And I press "Access My Courses"
  Then I should see an element with class of "user" within "3" seconds

  Scenario: I visit my registered courses	
    I access a registered course
    I click on "Courseware"
    I click on "Course Info"
    I click on "Discussion"
    I click on "Wiki"
    I click on "Progress"
    I click on "Instructor"