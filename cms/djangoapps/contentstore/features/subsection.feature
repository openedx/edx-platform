Feature: Create Subsection
  In order offer a course on the edX platform
  As a course author
  I want to create and edit subsections

  Scenario: Add a new subsection to a section
    Given I have opened a new course section in Studio
    When I click the New Subsection link
    And I enter the subsection name and click save
    Then I see my subsection on the Courseware page

  Scenario: Add a new subsection (with a name containing a quote) to a section (bug #216)
    Given I have opened a new course section in Studio
    When I click the New Subsection link
    And I enter a subsection name with a quote and click save
    Then I see my subsection name with a quote on the Courseware page
    And I click to edit the subsection name
    Then I see the complete subsection name with a quote in the editor

  Scenario: Assign grading type to a subsection and verify it is still shown after refresh (bug #258)
    Given I have opened a new course section in Studio
    And I have added a new subsection
    And I mark it as Homework
    Then I see it marked as Homework
    And I reload the page
    Then I see it marked as Homework

  Scenario: Set a due date in a different year (bug #256)
    Given I have opened a new subsection in Studio
    And I have set a release date and due date in different years
    Then I see the correct dates
    And I reload the page
    Then I see the correct dates

  Scenario: Delete a subsection
    Given I have opened a new course section in Studio
    And I have added a new subsection
    And I see my subsection on the Courseware page
    When I will confirm all alerts
    And I press the "subsection" delete icon
    And I confirm the prompt
    Then the subsection does not exist
