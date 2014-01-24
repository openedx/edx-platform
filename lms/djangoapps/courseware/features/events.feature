@shard_2
Feature: LMS.Events
  As a researcher, I want to be able to track events in the LMS

  Scenario Outline: An event is emitted for each request
    Given: I am registered for the course "6.002x"
    And I visit the url "<url>"
    Then a "<url>" server event is emitted

  Examples:
    | url                                        |
    | /dashboard                                 |
    | /courses/edx/6.002x/Test_Course/info       |
    | /courses/edx/6.002x/Test_Course/courseware |
