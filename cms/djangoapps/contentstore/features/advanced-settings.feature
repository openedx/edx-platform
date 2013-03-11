Feature: Advanced (manual) course policy
  In order to specify course policy settings for which no custom user interface exists
  I want to be able to manually enter JSON key/value pairs

#  Scenario: A course author sees default advanced settings
#    Given I have opened a new course in Studio
#    When I select the Advanced Settings
#    Then I see default advanced settings


#  Scenario: Test cancel editing key value
#    Given I am on the Advanced Course Settings page in Studio
#    When I edit the value of a policy key
#    And I press the "Cancel" notification button
#    Then the policy key value is unchanged
#

  Scenario: Test editing key value
    Given I am on the Advanced Course Settings page in Studio
    When I edit the value of a policy key
    And I press the "Save" notification button
    Then the policy key value is changed
#
#  Scenario: Add new entries, and they appear alphabetically after save
#    Given I am on the Advanced Course Settings page in Studio
#    When I create New Entries
#    Then they are alphabetized
#    And I reload the page
#    Then they are alphabetized
#
#  Scenario: Test how multi-line input appears
#    Given I am on the Advanced Course Settings page in Studio
#    When I create a JSON object
#    Then it is displayed as formatted
