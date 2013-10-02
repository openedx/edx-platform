@shard_2
Feature: Bulk Email
    As an instructor,
    In order to communicate with students and staff
    I want to send email to staff and students in a course.

    Scenario: Send bulk email
    Given I am an instructor for a course
    When I send email to "<Recipient>"
    Then Email is sent to "<Recipient>"

    Examples:
    | Recipient                        |
    | myself                           |
    | course staff                     |
    | students, staff, and instructors |
