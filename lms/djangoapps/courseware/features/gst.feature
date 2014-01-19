@shard_2
Feature: LMS.Graphical Slider Tool Module
  As a student, I want to view a Graphical Slider Tool Component

  Scenario: The slider changes values on the page
    Given that I have a course with a Graphical Slider Tool
    When I view the Graphical Slider Tool
    Then the displayed value should be 0
    And I move the slider to the right
    Then the displayed value should be 10