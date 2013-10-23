@shard_2
Feature: LMS.Bulk Email
    As an instructor or course staff,
    In order to communicate with students and staff
    I want to send email to staff and students in a course.

    Scenario: Send bulk email
    Given I am "<Role>" for a course
    When I send email to "<Recipient>"
    Then Email is sent to "<Recipient>"

    Examples:
    | Role          |  Recipient     |
    | instructor    |  myself        |
    | instructor    |  course staff  |
    | instructor    |  students, staff, and instructors  |
    | staff         |  myself        |
    | staff         |  course staff  |
    | staff         |  students, staff, and instructors  |
