Feature: Sign up and Sign out
  In order to create an account
  As someone who wants to use the site
  We'll see if I can create an account and log out

  Scenario: Visit the homepage to Sign Up
    Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
    ## "http://anant:agarwal@stage-edx-001.m.edx.org/"
    When I click "SIGN UP"
      And I signup with "bob62@bob.com" in the "email" field
      And I signup with "password" in the "password" field
      And I signup with "Bob62" in the "username" field
      And I signup with "Bob Jones" in the "name" field
#      And I select "None" from "level_of_education"
#      And I select "Male" from "gender"
#      And I select "1986" from "year_of_birth"
      And I click the checkbox "terms_of_service"
      And I click the checkbox "honor_code"
      And I login with "submit"
    Then I should see an element with class of "activation-message" within "3" seconds
      And I should see "Thanks For Registering!"


  Scenario: Logout of a signed in account
    Given I am logged in
    When I click the "▾" dropdown
      And I click "Log Out"
    Then I should see an element with id of "login" within "3" seconds
