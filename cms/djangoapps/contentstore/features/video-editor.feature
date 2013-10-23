@shard_3
Feature: CMS.Video Component Editor
  As a course author, I want to be able to create video components.

  Scenario: User can view Video metadata
    Given I have created a Video component
    And I edit the component
    Then I see the correct video settings and default values

  # Safari has trouble saving values on Sauce
  @skip_safari
  Scenario: User can modify Video display name
    Given I have created a Video component
    And I edit the component
    Then I can modify the display name
    And my video display name change is persisted on save

  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are hidden when "show captions" is false
    Given I have created a Video component with subtitles
    And I have set "show transcript" to False
    Then when I view the video it does not show the captions

  # Sauce Labs cannot delete cookies
  @skip_sauce
  Scenario: Captions are shown when "show captions" is true
    Given I have created a Video component with subtitles
    And I have set "show transcript" to True
    Then when I view the video it does show the captions
