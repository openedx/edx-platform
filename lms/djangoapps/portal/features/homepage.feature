Feature: Homepage for web users
  In order to get an idea what edX is about
  As a an anonymous web user
  I want to check the information on the home page

  Scenario: User can see the "Login" button
    Given I visit the homepage
    Then I should see a link called "Log In"

  Scenario: User can see the "Sign up" button
    Given I visit the homepage
    Then I should see a link called "Sign Up"

  Scenario Outline: User can see main parts of the page
    Given I visit the homepage
    Then I should see a link called "<Link>"
    When I click the link with the text "<Link>"
    Then I should see that the path is "<Path>"

    Examples:
    | Link         | Path     |
    | Find Courses | /courses |
    | About        | /about   |
    | Jobs         | /jobs    |
    | Contact      | /contact |

  Scenario: User can visit the blog
    Given I visit the homepage
    When I click the link with the text "Blog"
    Then I should see that the url is "http://blog.edx.org/"

  # TODO: test according to domain or policy
  Scenario: User can see the partner institutions
    Given I visit the homepage
    Then I should see "<Partner>" in the Partners section

    Examples:
    | Partner     |
    | MITx        |
    | HarvardX    |
    | BerkeleyX   |
    | UTx         |    
    | WellesleyX  |
    | GeorgetownX |  

  # # TODO: Add scenario that tests the courses available
  # # using a policy or a configuration file
