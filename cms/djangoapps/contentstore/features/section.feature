@shard_2
Feature: CMS.Create Section
  In order offer a course on the edX platform
  As a course author
  I want to create and edit sections

  Scenario: Add a new section to a course
    Given I have opened a new course in Studio
    When I click the New Section link
    And I enter the section name and click save
    Then I see my section on the Courseware page
    And I see a release date for my section
    And I see a link to create a new subsection

  Scenario: Add a new section (with a quote in the name) to a course (bug #216)
    Given I have opened a new course in Studio
    When I click the New Section link
    And I enter a section name with a quote and click save
    Then I see my section name with a quote on the Courseware page
    And I click to edit the section name
    Then I see the complete section name with a quote in the editor

  Scenario: Edit section release date
    Given I have opened a new course in Studio
    And I have added a new section
    When I click the Edit link for the release date
    And I set the section release date to 12/25/2013
    Then the section release date is updated
    And I see a "saving" notification

  Scenario: Section name not clickable on editing release date
    Given I have opened a new course in Studio
    And I have added a new section
    When I click the Edit link for the release date
    And I click on section name in Section Release Date modal
    Then I see no form for editing section name in modal

  Scenario: Delete section
    Given I have opened a new course in Studio
    And I have added a new section
    When I will confirm all alerts
    And I press the "section" delete icon
    And I confirm the prompt
    Then the section does not exist
