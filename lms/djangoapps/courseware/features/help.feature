Feature: LMS.The help module should work
  In order to get help
  As a student
  I want to be able to report a problem


  Scenario: I can submit a problem when I am not logged in
    Given I visit the homepage
    When I open the help form
    And I report a "<FeedbackType>"
    Then I should see confirmation that the issue was received

        Examples:
        | FeedbackType      |
        | problem           |
        | suggestion        |
        | question          |


  Scenario: I can submit a problem when I am logged in
    Given I am in a course
    When I open the help form
    And I report a "<FeedbackType>" without saying who I am
    Then I should see confirmation that the issue was received

        Examples:
        | FeedbackType      |
        | problem           |
        | suggestion        |
        | question          |

