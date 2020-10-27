@shard_1
Feature: CMS.Problem Editor
  As a course author, I want to be able to create problems and edit their settings.

  Scenario: User can revert display name to unset
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I can revert the display name to unset
    And my display name is unset on save

  Scenario: User can specify html in display name and it will be escaped
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I can specify html in the display name and save
    And the problem display name is "<script>alert('test')</script>"

  # IE will not click the revert button properly
  @skip_internetexplorer
  Scenario: User can select values in a Select
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I can select Per Student for Randomization
    And my change to randomization is persisted
    And I can revert to the default value for randomization

  # Safari will input it as 35.
  @skip_safari
  Scenario: User can modify float input values
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I can set the weight to "3.5"
    And my change to weight is persisted
    And I can revert to the default value of unset for weight

  Scenario: User cannot type letters in float number field
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then if I set the weight to "abc", it remains unset

  # Safari will input it as 234.
  @skip_safari
  Scenario: User cannot type decimal values integer number field
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then if I set the max attempts to "2.34", it will persist as a valid integer

  # Safari will input it incorrectly
  @skip_safari
  Scenario: User cannot type out of range values in an integer number field
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then if I set the max attempts to "-3", it will persist as a valid integer

  # Safari will input it as 35.
  @skip_safari
  Scenario: Settings changes are not saved on Cancel
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I can set the weight to "3.5"
    And I can modify the display name
    Then If I press Cancel my changes are not persisted

  Scenario: Cheat sheet visible on toggle
    Given I have created a Blank Common Problem
    And I can edit the problem
    Then I can see cheatsheet
