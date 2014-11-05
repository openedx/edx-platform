@shard_1
Feature: LMS.Register for a course
  As a registered user
  In order to access my class content
  I want to register for a class on the edX website

  Scenario: I can register for a course
    Given The course "6.002x" exists
    And I am logged in
    And I visit the courses page
    When I register for the course "6.002x"
    Then I should see the course numbered "6.002x" in my dashboard
    And a "edx.course.enrollment.activated" server event is emitted

  Scenario: I can unenroll from a course
    Given I am registered for the course "6.002x"
    And I visit the dashboard
    Then I should see the course numbered "6.002x" in my dashboard
    When I unenroll from the course numbered "6.002x"
    Then I should be on the dashboard page
    And I should see an empty dashboard message
    And I should NOT see the course numbered "6.002x" in my dashboard
    And a "edx.course.enrollment.deactivated" server event is emitted
