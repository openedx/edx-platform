Feature: Video Component Editor
  As a course author, I want to be able to create video components.

  Scenario: User can view metadata
    Given I have created a Video component
    And I edit and select Settings
    Then I see only the Video display name setting

  Scenario: User can modify display name
    Given I have created a Video component
    And I edit and select Settings
    Then I can modify the display name
    And my display name change is persisted on save
