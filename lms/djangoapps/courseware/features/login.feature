@shard_1
Feature: LMS.Login in as a registered user
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

    # firefox will not redirect properly when the whole suite is run
    @skip_firefox
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

    Scenario: Login with valid redirect
    Given I am an edX user
    And The course "6.002x" exists
    And I am registered for the course "6.002x"
    And I am not logged in
    And I visit the url "/courses/edx/6.002x/Test_Course/courseware"
    And I should see that the path is "/accounts/login?next=/courses/edx/6.002x/Test_Course/courseware"
    When I submit my credentials on the login form
    And I wait for "2" seconds
    Then the page title should contain "6.002x Courseware"

    Scenario: Login with an invalid redirect
    Given I am an edX user
    And I am not logged in
    And I visit the url "/login?next=http://www.google.com/"
    When I submit my credentials on the login form
    Then I should be on the dashboard page

    Scenario: Login with a redirect with parameters
    Given I am an edX user
    And I am not logged in
    And I visit the url "/debug/show_parameters?foo=hello&bar=world"
    And I should see that the path is "/accounts/login?next=/debug/show_parameters%3Ffoo%3Dhello%26bar%3Dworld"
    When I submit my credentials on the login form
    And I wait for "2" seconds
    Then I should see "foo: u'hello'" somewhere on the page
    And I should see "bar: u'world'" somewhere on the page
