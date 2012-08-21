Feature: Login
	In order to login
  As a registered user
  We'll see if I can log in to my account and perform user actions

    Scenario: Login to an existing account and logout
    Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
    #"http://anant:agarwal@stage-edx-001.m.edx.org/"
    When I click "LOG IN"
      And I login with "ddieker@gmail.com" in the "email" field
      And I login with "password" in the "password" field
      And I press "Access My Courses"
    Then I should see an element with class of "user" within "3" seconds

  	Scenario: I register for a course, unregister, then register again
  	Given I have a list of courses
  	When I click "Find Courses"
  		And I register for every course
  		And I notice I have been registered for every course
  		And I unregister for every course
  		And I notice I have been unregistered
  		And I register for one course
  	Then I should see that course in my dashboard

    Scenario: Logout of a signed in account
    Given I am logged in
    When I click the "▾" dropdown
      And I click "Log Out"
    Then I should see an element with id of "login" within "3" seconds