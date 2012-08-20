Feature: Homepage renders
  In order to create an account
  As someone who wants to use the site
  We'll see if I can create an account

  Scenario: Visit the homepage to Sign Up
    #Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
    Given I visit "http://edx.org/"
    When I click "SIGN UP"
      And I signup with "bob@bob.com" in the "email" field
      And I signup with "password" in the "password" field
      And I fill in "username" with "Bjones1986"
      And I fill in "name" with "Bob Jones"
      #And I select "Master\'s or professional degree" from "level_of_education"
      #And I select the option "(.*)" from the selection "(.*)"
      #And I check "terms_of_service"
      #And I check "honor_code"
      #And I click "CREATE MY ACCOUNT"