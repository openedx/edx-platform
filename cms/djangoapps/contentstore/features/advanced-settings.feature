Feature: Advanced (manual) course policy
  In order to specify course policy settings for which no custom user interface exists
  I want to be able to manually enter JSON key/value pairs

  Scenario: A course author sees only display_name on a newly created course
    Given I have opened a new course in Studio
    When I select the Advanced Settings
    Then I see only the display name

  Scenario: Test if there are no policy settings without existing UI controls
    Given I have opened a new course in Studio
    When I select the Advanced Settings
    And I delete the display name
    Then there are no advanced policy settings
    And I reload the page
    Then there are no advanced policy settings

  Scenario: Add new entries, and they appear alphabetically after save
    Given I have opened a new course in Studio
    When I select the Advanced Settings
    And I create New Entries
    Then they are alphabetized
    And I reload the page
    Then they are alphabetized

  Scenario: Test how multi-line input appears
    Given I have opened a new course in Studio
    When I select the Advanced Settings
    And I create a JSON object
    Then it is displayed as formatted

