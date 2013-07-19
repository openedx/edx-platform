Feature: Video Alpha Component
  As a course author, I want to be able to view my created videos in Studio.

  Scenario: Autoplay is disabled in Studio
    Given I have created a Video Alpha component
    Then when I view the video alpha it does not have autoplay enabled
