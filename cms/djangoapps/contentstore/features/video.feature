Feature: Video Component
  As a course author, I want to be able to view my created videos in Studio.

  Scenario: Autoplay is disabled in Studio
    Given I have created a Video component
    Then when I view the video it does not have autoplay enabled
