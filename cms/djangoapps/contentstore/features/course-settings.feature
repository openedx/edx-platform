@shard_2
Feature: CMS.Course Settings
  As a course author, I want to be able to configure my course settings.

  # Safari has trouble keeps dates on refresh
  @skip_safari
  Scenario: User can set course dates
    Given I have opened a new course in Studio
    When I select Schedule and Details
    And I set course dates
    And I press the "Save" notification button
    And I reload the page
    Then I see the set dates

    # IE has trouble with saving information
    @skip_internetexplorer
  Scenario: User can clear previously set course dates (except start date)
    Given I have set course dates
    And I clear all the dates except start
    And I press the "Save" notification button
    And I reload the page
    Then I see cleared dates

    # IE has trouble with saving information
    @skip_internetexplorer
  Scenario: User cannot clear the course start date
    Given I have set course dates
    And I press the "Save" notification button
    And I clear the course start date
    Then I receive a warning about course start date
    And I reload the page
    And the previously set start date is shown

    # IE has trouble with saving information
    # Safari gets CSRF token errors
    @skip_internetexplorer
    @skip_safari
  Scenario: User can correct the course start date warning
    Given I have tried to clear the course start
    And I have entered a new course start date
    And I press the "Save" notification button
    Then The warning about course start date goes away
    And I reload the page
    Then my new course start date is shown

  # Safari does not save + refresh properly through sauce labs
  @skip_safari
  Scenario: Settings are only persisted when saved
    Given I have set course dates
    And I press the "Save" notification button
    When I change fields
    And I reload the page
    Then I do not see the changes

  # Safari does not save + refresh properly through sauce labs
  @skip_safari
  Scenario: Settings are reset on cancel
    Given I have set course dates
    And I press the "Save" notification button
    When I change fields
    And I press the "Cancel" notification button
    Then I do not see the changes

  # Safari gets CSRF token errors
  @skip_safari
  Scenario: Confirmation is shown on save
    Given I have opened a new course in Studio
    When I select Schedule and Details
    And I change the "<field>" field to "<value>"
    And I press the "Save" notification button
    Then I see a confirmation that my changes have been saved
    # Lettuce hooks don't get called between each example, so we need
    # to run the before.each_scenario hook manually to avoid database
    # errors.
    And I reset the database

  Examples:
    | field                     | value             |
    | Course Start Time         | 11:00             |
    | Course Introduction Video | 4r7wHMg5Yjg       |
    | Course Effort             | 200:00            |
    | Course Image URL          | image.jpg         |

  # Special case because we have to type in code mirror
  Scenario: Changes in Course Overview show a confirmation
    Given I have opened a new course in Studio
    When I select Schedule and Details
    And I change the course overview
    And I press the "Save" notification button
    Then I see a confirmation that my changes have been saved

  Scenario: User cannot save invalid settings
    Given I have opened a new course in Studio
    When I select Schedule and Details
    And I change the "Course Start Date" field to ""
    Then the save notification button is disabled

  Scenario: User can upload course image
    Given I have opened a new course in Studio
    When I select Schedule and Details
    And I click the "Upload Course Image" button
    And I upload a new course image
    Then I should see the new course image
    And the image URL should be present in the field
