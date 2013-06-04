Feature: HTML Editor
  As a course author, I want to be able to create HTML blocks.

  Scenario: User can view metadata
    Given I have created a Blank HTML Page
    And I edit and select Settings
    Then I see only the HTML display name setting

  Scenario: User can modify display name
    Given I have created a Blank HTML Page
    And I edit and select Settings
    Then I can modify the display name
    And my display name change is persisted on save
