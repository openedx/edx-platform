Feature: Login in as a registered user
  As a registered user
  In order to access my content
  I want to be able to login in to edX

    Scenario: Login to an unactivated account
    Given I am an edX user
    And I am an unactivated user
    And I visit the homepage
    When I click the link with the text "Log in"
    And I submit my credentials on the login form
    Then I should see the login error message "This account has not been activated"

    Scenario: Login to an activated account
    Given I am an edX user
    And I am an activated user
    And I visit the homepage
    When I click the link with the text "Log in"
    And I submit my credentials on the login form
    Then I should be on the dashboard page

    Scenario: Logout of a signed in account
    Given I am logged in
    When I click the dropdown arrow
    And I click the link with the text "Log Out"
    Then I should see a link with the text "Log in"
    And I should see that the path is "/"
