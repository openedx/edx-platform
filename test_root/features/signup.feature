Feature: Homepage renders
  In order to create an account
  As someone who wants to use the site
  We'll see if I can create an account

  Scenario: Visit the homepage to Sign Up
    Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
    When I click "SIGN UP"
      And I signup with "bob14@bob.com" in the "email" field
      And I signup with "password" in the "password" field
      And I fill in "username" with "Bjones1986"
      And I fill in "name" with "Bob Jones"
      #And I select "Master\'s or professional degree" from "level_of_education"
      #And I select the option "(.*)" from the selection "(.*)"
      And I click the checkbox "terms_of_service"
      And I click the checkbox "honor_code"
      And I press "Create My Account"
    Then I should see an element with class of "activation-message" within "10" seconds
      And I should see "Thanks For Registering!"

  Scenario: Logout of a signed in account
    Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/dashboard"
    When I logout
    Then I should see an element with id of "login" within "3" seconds

  Scenario: Login to an existing account and logout
    Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
    When I click "LOG IN"
      And I login with "test@test.com" in the "email" field
      And I login with "password" in the "password" field
      And I press "Access My Courses"
    Then The browser's URL should contain "\/dashboard" within 3 seconds