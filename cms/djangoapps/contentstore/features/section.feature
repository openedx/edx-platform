Feature: Create Section
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

  Scenario: Edit section release date
    Given I have opened a new course in Studio
    And I have added a new section
    When I click the Edit link for the release date
    And I save a new section release date
    Then the section release date is updated

  Scenario: Delete section
    Given I have opened a new course in Studio
    And I have added a new section
    When I press the "section" delete icon
    And I confirm the alert
    Then the section does not exist