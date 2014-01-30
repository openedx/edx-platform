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
    And I reload the page
    Then the correct Youtube video is shown

  # 7
  # Disabled 11/26 due to flakiness in master.
  # Enabled back on 11/29.
  Scenario: When enter key is pressed on a caption shows an outline around it
    Given I have created a Video component with subtitles
    And Make sure captions are opened
    Then I focus on caption line with data-index "0"
    Then I press "enter" button on caption line with data-index "0"
    And I see caption line with data-index "0" has class "focused"

  # 8
  Scenario: When start end end times are specified, a range on slider is shown
    Given I have created a Video component with subtitles
    And Make sure captions are closed
    And I edit the component
    And I open tab "Advanced"
    And I set value "00:00:12" to the field "Start Time"
    And I set value "00:00:24" to the field "End Time"
    And I save changes
    And I click video button "play"
    Then I see a range on slider
