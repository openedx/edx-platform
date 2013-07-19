Feature: Video Alpha Component Editor
  As a course author, I want to be able to create videoalpha components.

  Scenario: User can view metadata
    Given I have created a Video Alpha component
    And I edit and select Settings
    Then I see the correct videoalpha settings and default values

  Scenario: User can modify display name
    Given I have created a Video Alpha component
    And I edit and select Settings
    Then I can modify the display name
    And my display name change is persisted on save

  @skip
  Scenario: Captions are hidden when "show captions" is false
    Given I have created a Video component
    And I have set "show captions" to False
    Then when I view the video it does not show the captions

  @skip
  Scenario: Captions are shown when "show captions" is true
    Given I have created a Video component
    And I have set "show captions" to True
    Then when I view the video it does show the captions
