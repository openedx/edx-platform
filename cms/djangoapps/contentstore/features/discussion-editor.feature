Feature: Discussion Component Editor
  As a course author, I want to be able to create discussion components.

  Scenario: User can view metadata
    Given I have created a Discussion Tag
    And I edit and select Settings
    Then I see three alphabetized settings and their expected values

  Scenario: User can modify display name
    Given I have created a Discussion Tag
    And I edit and select Settings
    Then I can modify the display name
    And my display name change is persisted on save

  Scenario: Creating a discussion takes a single click
    Given I have clicked the new unit button
    Then creating a discussion takes a single click
