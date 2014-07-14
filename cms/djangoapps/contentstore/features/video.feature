@shard_3 @requires_stub_youtube
Feature: CMS Video Component
  As a course author, I want to be able to view my created videos in Studio

  # 1
  Scenario: YouTube stub server proxies YouTube API correctly
    Given youtube stub server proxies YouTube API
    And I have created a Video component
    Then I can see video button "play"
    And I click video button "play"
    Then I can see video button "pause"

  # 2
  Scenario: YouTube stub server can block YouTube API
    Given youtube stub server blocks YouTube API
    And I have created a Video component
    And I wait for "3" seconds
    Then I do not see video button "play"

  # 3
  Scenario: Autoplay is disabled in Studio
    Given I have created a Video component
    Then when I view the video it does not have autoplay enabled

  # 4
  Scenario: Creating a video takes a single click
    Given I have clicked the new unit button
    Then creating a video takes a single click

  # 5
  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are hidden correctly
    Given I have created a Video component with subtitles
    And I have hidden captions
    Then when I view the video it does not show the captions

  # 6
  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are shown correctly
    Given I have created a Video component with subtitles
    Then when I view the video it does show the captions

  # 7
  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are toggled correctly
    Given I have created a Video component with subtitles
    And I have toggled captions
    Then when I view the video it does show the captions

  # 8
  Scenario: Video data is shown correctly
    Given I have created a video with only XML data
    And I reload the page
    Then the correct Youtube video is shown

  # 9
  # Disabled 11/26 due to flakiness in master.
  # Enabled back on 11/29.
  Scenario: When enter key is pressed on a caption shows an outline around it
    Given I have created a Video component with subtitles
    And Make sure captions are opened
    Then I focus on caption line with data-index "0"
    Then I press "enter" button on caption line with data-index "0"
    And I see caption line with data-index "0" has class "focused"

  # 10
  Scenario: When start and end times are specified, a range on slider is shown
    Given I have created a Video component with subtitles
    And Make sure captions are closed
    And I edit the component
    And I open tab "Advanced"
    And I set value "00:00:12" to the field "Video Start Time"
    And I set value "00:00:24" to the field "Video Stop Time"
    And I save changes
    And I click video button "play"
    Then I see a range on slider

  # 11
  # Disabled 2/19/14 after intermittent failures in master
  #Scenario: Check that position is stored on page refresh, position within start-end range
  #  Given I have created a Video component with subtitles
  #  And Make sure captions are closed
  #  And I edit the component
  #  And I open tab "Advanced"
  #  And I set value "00:00:12" to the field "Video Start Time"
  #  And I set value "00:00:24" to the field "Video Stop Time"
  #  And I save changes
  #  And I click video button "play"
  #  Then I see a range on slider
  #  Then I seek video to "16" seconds
  #  And I click video button "pause"
  #  And I reload the page
  #  And I click video button "play"
  #  Then I see video starts playing from "0:16" position

  # 12
# Disabled 2/18/14 after intermittent failures in master
#  Scenario: Check that position is stored on page refresh, position before start-end range
#    Given I have created a Video component with subtitles
#    And Make sure captions are closed
#    And I edit the component
#    And I open tab "Advanced"
#    And I set value "00:00:12" to the field "Video Start Time"
#    And I set value "00:00:24" to the field "Video Stop Time"
#    And I save changes
#    And I click video button "play"
#    Then I see a range on slider
#    Then I seek video to "5" seconds
#    And I click video button "pause"
#    And I reload the page
#    And I click video button "play"
#    Then I see video starts playing from "0:12" position

  # 13
# Disabled 2/18/14 after intermittent failures in master
#  Scenario: Check that position is stored on page refresh, position after start-end range
#    Given I have created a Video component with subtitles
#    And Make sure captions are closed
#    And I edit the component
#    And I open tab "Advanced"
#    And I set value "00:00:12" to the field "Video Start Time"
#    And I set value "00:00:24" to the field "Video Stop Time"
#    And I save changes
#    And I click video button "play"
#    Then I see a range on slider
#    Then I seek video to "30" seconds
#    And I click video button "pause"
#    And I reload the page
#    And I click video button "play"
#    Then I see video starts playing from "0:12" position
