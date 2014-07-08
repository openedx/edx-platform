@shard_1
Feature: CMS.Advanced (manual) course policy
  In order to specify course policy settings for which no custom user interface exists
  I want to be able to manually enter JSON key /value pairs


  Scenario: A course author sees default advanced settings
    Given I have opened a new course in Studio
    When I select the Advanced Settings
    Then I see default advanced settings

  Scenario: Add new entries, and they appear alphabetically after save
    Given I am on the Advanced Course Settings page in Studio
    Then the settings are alphabetized

  # Sauce labs does not play nicely with CodeMirror
  @skip_sauce
  Scenario: Test cancel editing key value
    Given I am on the Advanced Course Settings page in Studio
    When I edit the value of a policy key
    And I press the "Cancel" notification button
    Then the policy key value is unchanged
    And I reload the page
    Then the policy key value is unchanged

  # Sauce labs does not play nicely with CodeMirror
  @skip_sauce
  Scenario: Test editing key value
    Given I am on the Advanced Course Settings page in Studio
    When I edit the value of a policy key and save
    Then the policy key value is changed
    And I reload the page
    Then the policy key value is changed

  # Sauce labs does not play nicely with CodeMirror
  @skip_sauce
  Scenario: Test how multi-line input appears
    Given I am on the Advanced Course Settings page in Studio
    When I create a JSON object as a value for "Discussion Topic Mapping"
    Then it is displayed as formatted
    And I reload the page
    Then it is displayed as formatted

  # Sauce labs does not play nicely with CodeMirror
  @skip_sauce
  Scenario: Test error if value supplied is of the wrong type
    Given I am on the Advanced Course Settings page in Studio
    When I create a JSON object as a value for "Course Display Name"
    Then I get an error on save
    And I reload the page
    Then the policy key value is unchanged

  # This feature will work in Firefox only when Firefox is the active window
  # Sauce labs does not play nicely with CodeMirror
  @skip_sauce
  Scenario: Test automatic quoting of non-JSON values
    Given I am on the Advanced Course Settings page in Studio
    When I create a non-JSON value not in quotes
    Then it is displayed as a string
    And I reload the page
    Then it is displayed as a string

  # Sauce labs does not play nicely with CodeMirror
  @skip_sauce
  Scenario: Confirmation is shown on save
    Given I am on the Advanced Course Settings page in Studio
    When I edit the value of a policy key
    And I press the "Save" notification button
    Then I see a confirmation that my changes have been saved

  Scenario: Deprecated Settings are not shown by default
    Given I am on the Advanced Course Settings page in Studio
    Then deprecated settings are not shown

  Scenario: Deprecated Settings can be toggled
    Given I am on the Advanced Course Settings page in Studio
    When I toggle the display of deprecated settings
    Then deprecated settings are then shown
    And I toggle the display of deprecated settings
    Then deprecated settings are not shown
