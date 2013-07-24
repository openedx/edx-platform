Feature: Video Component
  As a course author, I want to be able to view my created videos in Studio.

  Scenario: Autoplay is disabled in Studio
    Given I have created a Video component
    Then when I view the video it does not have autoplay enabled

  Scenario: Creating a video takes a single click
    Given I have clicked the new unit button
    Then creating a video takes a single click

  Scenario: Captions are hidden correctly
    Given I have created a Video component
    And I have hidden captions
    Then when I view the video it does not show the captions

  Scenario: Captions are shown correctly
    Given I have created a Video component
    Then when I view the video it does show the captions

  Scenario: Captions are toggled correctly
    Given I have created a Video component
    And I have toggled captions
    Then when I view the video it does show the captions

  Scenario: Autoplay is disabled in Studio for Video Alpha
    Given I have created a Video Alpha component
    Then when I view the videoalpha it does not have autoplay enabled

  Scenario: User can view Video Alpha metadata
    Given I have created a Video Alpha component
    And I edit and select Settings
    Then I see the correct videoalpha settings and default values

  Scenario: User can modify Video Alpha display name
    Given I have created a Video Alpha component
    And I edit and select Settings
    Then I can modify the display name
    And my display name change is persisted on save

  @skip
  Scenario: Video Alpha captions are hidden when "show captions" is false
    Given I have created a Video Alpha component
    And I have set "show captions" to False
    Then when I view the video it does not show the captions

  @skip
  Scenario: Video Alpha captions are shown when "show captions" is true
    Given I have created a Video Alpha component
    And I have set "show captions" to True
    Then when I view the video it does show the captions
