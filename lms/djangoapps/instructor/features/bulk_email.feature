@shard_2
Feature: LMS.Instructor Dash Bulk Email
    As an instructor or course staff,
    In order to communicate with students and staff
    I want to send email to staff and students in a course.

    Scenario: Send bulk email
    Given there is a course with a staff, instructor and student
    And I am logged in to the course as "<Role>"
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
