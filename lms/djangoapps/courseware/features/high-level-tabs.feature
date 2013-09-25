@shard_1
Feature: LMS.All the high level tabs should work
  In order to preview the courseware
  As a student
  I want to navigate through the high level tabs

Scenario: I can navigate to all high - level tabs in a course
        Given: I am registered for the course "6.002x"
        And The course "6.002x" has extra tab "Custom Tab"
        And I am logged in
        And I click on View Courseware
        When I click on the tabs then the page title should contain the following titles:
        | TabName       | PageTitle             |
        | Courseware    | 6.002x Courseware     |
        | Course Info   | 6.002x Course Info    |
        | Custom Tab    | 6.002x Custom Tab     |
        | Wiki          | edX Wiki              |
        | Progress      | 6.002x Progress       |
