Feature: Advanced (manual) course policy
  In order to specify course policy settings for which no custom user interface exists
  I want to be able to manually enter JSON key/value pairs

  Scenario: A course author sees only display_name on a newly created course
    Given I have opened a new course in Studio
    When I select the Advanced Settings
    Then I see only the display name

  Scenario: A course author sees something sensible if there are no policy settings without existing UI controls
    Given I have opened a new course in Studio
    When I select the Advanced Settings
    And I delete the display name
    Then There are no advanced policy settings
    And I refresh and select the Advanced Settings
    Then There are no advanced policy settings

  Scenario: A course author can add new entries, and they appear alphabetically after save
     Given I have opened a new course in Studio
     When I select the Advanced Settings
     And Create New Entries
     Then They are alphabetized
     And I refresh and select the Advanced Settings
     Then They are alphabetized