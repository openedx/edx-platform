@shard_1
Feature: LMS.Homepage for web users
  In order to get an idea what edX is about
  As an anonymous web user
  I want to check the information on the home page

  Scenario: User can see the "Sign in" button
    Given I visit the homepage
    Then I should see a link called "Sign in"

  Scenario: User can see the "Register" button
    Given I visit the homepage
    Then I should see a link called "Register"

  Scenario Outline: User can see main parts of the page
    Given I visit the homepage
    Then I should see the following links and ids
    | id          | Link        |
    | about       | About       |
    | careers     | Careers     |
    | help-center | Help Center |
    | contact     | Contact     |
    | news        | News        |
