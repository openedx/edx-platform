Feature: Problem Editor
  As a course author, I want to be able to create problems and edit their settings.

  Scenario: User can view metadata
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I see five alphabetized settings and their expected values
    And Edit High Level Source is not visible

  Scenario: User can modify String values
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I can modify the display name
    And my display name change is persisted on save

  Scenario: User can specify special characters in String values
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I can specify special characters in the display name
    And my special characters and persisted on save

  Scenario: User can revert display name to unset
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I can revert the display name to unset
    And my display name is unset on save

  Scenario: User can select values in a Select
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I can select Per Student for Randomization
    And my change to randomization is persisted
    And I can revert to the default value for randomization

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

  Scenario: User cannot type decimal values integer number field
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then if I set the max attempts to "2.34", it displays initially as "234", and is persisted as "234"

  Scenario: User cannot type out of range values in an integer number field
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then if I set the max attempts to "-3", it displays initially as "-3", and is persisted as "0"

  Scenario: Settings changes are not saved on Cancel
    Given I have created a Blank Common Problem
    When I edit and select Settings
    Then I can set the weight to "3.5"
    And I can modify the display name
    Then If I press Cancel my changes are not persisted

  Scenario: Edit High Level source is available for LaTeX problem
    Given I have created a LaTeX Problem
    When I edit and select Settings
    Then Edit High Level Source is visible

  Scenario: High Level source is persisted for LaTeX problem (bug STUD-280)
    Given I have created a LaTeX Problem
    When I edit and compile the High Level Source
    Then my change to the High Level Source is persisted
    And when I view the High Level Source I see my changes
