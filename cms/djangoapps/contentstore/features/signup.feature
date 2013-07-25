Feature: Sign in
  In order to use the edX content
  As a new user
  I want to signup for a student account

  Scenario: Sign up from the homepage
    Given I visit the Studio homepage
    When I click the link with the text "Sign Up"
    And I fill in the registration form
    And I press the Create My Account button on the registration form
    Then I should see be on the studio home page
    And I should see the message "complete your sign up we need you to verify your email address"
