Feature: Homepage renders
  In order to get an idea of edX
  As anonymous web users
  We want to see lots of information about edX on the home page

  Scenario: We can see all the courses
    Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
    I should see "3.091x"
    I should see "CS50x"
    I should see "CS169.1x"
    I should see "6.002x"
    I should see "PH207x"
    I should see "CS188.1x"
    I should see "6.00x"

  Scenario: We can see the "Login" button
    Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
    I should see "Sign Up"

  Scenario: We can see the "Sign up" button
    Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
    I should see "Log In"

  Scenario: We can see the three partner institutions
    Given I visit "http://anant:agarwal@stage-edx-001.m.edx.org/"
    I should see "MITx"
    I should see "HarvardX"
    I should see "BerkeleyX"