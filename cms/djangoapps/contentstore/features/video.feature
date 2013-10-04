@shard_3
Feature: CMS.Video Component
  As a course author, I want to be able to view my created videos in Studio.

  # Video Alpha Features will work in Firefox only when Firefox is the active window
  Scenario: Autoplay is disabled in Studio
    Given I have created a Video component
    Then when I view the video it does not have autoplay enabled

  Scenario: Creating a video takes a single click
    Given I have clicked the new unit button
    Then creating a video takes a single click

  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are hidden correctly
    Given I have created a Video component with subtitles
    And I have hidden captions
    Then when I view the video it does not show the captions

  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are shown correctly
    Given I have created a Video component with subtitles
    Then when I view the video it does show the captions

  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are toggled correctly
    Given I have created a Video component with subtitles
    And I have toggled captions
    Then when I view the video it does show the captions

  Scenario: Video data is shown correctly
    Given I have created a video with only XML data
    And I reload the page
    Then the correct Youtube video is shown
