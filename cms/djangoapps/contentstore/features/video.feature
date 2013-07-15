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
