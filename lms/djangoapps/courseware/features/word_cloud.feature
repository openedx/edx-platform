@shard_2
Feature: LMS.World Cloud component
  As a student, I want to view Word Cloud component in LMS.

  Scenario: Word Cloud component in LMS is rendered with empty result
    Given the course has a Word Cloud component
    Then I view the word cloud and it has rendered
    When I press the Save button
    Then I see the empty result

  Scenario: Word Cloud component in LMS is rendered with result
    Given the course has a Word Cloud component
    Then I view the word cloud and it has rendered
    When I fill inputs
    And I press the Save button
    Then I see the result with words count
