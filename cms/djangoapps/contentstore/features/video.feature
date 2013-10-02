@shard_3
Feature: CMS.Video Component
  As a course author, I want to be able to view my created videos in Studio.

  # 1
  # Video Alpha Features will work in Firefox only when Firefox is the active window
  Scenario: Autoplay is disabled in Studio
    Given I have created a Video component
    Then when I view the video it does not have autoplay enabled

  # 2
  Scenario: Creating a video takes a single click
    Given I have clicked the new unit button
    Then creating a video takes a single click

  # 3
  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are hidden correctly
    Given I have created a Video component with subtitles
    And I have hidden captions
    Then when I view the video it does not show the captions

  # 4
  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are shown correctly
    Given I have created a Video component with subtitles
    Then when I view the video it does show the captions

  # 5
  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are toggled correctly
    Given I have created a Video component with subtitles
    And I have toggled captions
    Then when I view the video it does show the captions

  # 6
  Scenario: Video data is shown correctly
    Given I have created a video with only XML data
    Then the correct Youtube video is shown

  # 7
  Scenario: Closed captions become visible when the mouse hovers over CC button
    Given I have created a Video component with subtitles
    And Make sure captions are closed
    Then Captions become invisible
    And Hover over CC button
    Then Captions become visible

  # 8
  Scenario: Open captions never become invisible
    Given I have created a Video component with subtitles
    And Make sure captions are open
    Then Captions become visible
    And Hover over CC button
    Then Captions become visible
    And Hover over volume button
    Then Captions become visible
