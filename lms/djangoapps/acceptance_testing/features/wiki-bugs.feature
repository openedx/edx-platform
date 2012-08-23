Feature: There are bugs on the wiki
  In order to see if bugs are fixed
  As a developer
  I want to test known bad pages to see if they render properly


  Scenario: Login to an existing account
  Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
  When I click "LOG IN"
    And I login with "ddieker+admin@gmail.com" in the "email" field
    And I login with "password" in the "password" field
    And I press "Access My Courses"
  Then I should see an element with class of "user" within "3" seconds

  Scenario: See all children when there are children crashes
  Given I visit "http://stage-edx-001.m.edx.org/courses/MITx/6.002x/2012_Fall/wiki/6.002x/"
  	And I click "See all children"
  	And I click on a child
  Then I should not get a server error
  
  Scenario: See All Children when there are no children crashes
  Given I visit "http://stage-edx-001.m.edx.org/courses/BerkeleyX/CS188.1x/2012_Fall/wiki/CS188.1x/"
    And I click "See all children"
  Then I should not get a server error