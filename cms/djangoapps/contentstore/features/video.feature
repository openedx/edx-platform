@shard_3 @requires_stub_youtube
Feature: CMS Video Component
  As a course author, I want to be able to view my created videos in Studio

  # 2
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

  # 3
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

  # 4
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
