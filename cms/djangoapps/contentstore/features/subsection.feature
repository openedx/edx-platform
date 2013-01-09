Feature: Create Subsection
  In order offer a course on the edX platform
  As a course author
  I want to create and edit subsections

    Scenario: Add a new subsection to a section
    Given I have opened a new course section in Studio
    When I click the New Subsection link
    And I enter the subsection name and click save
    Then I see my subsection on the Courseware page

    Scenario: Delete a subsection
    Given I have opened a new course section in Studio
    And I have added a new subsection
    And I see my subsection on the Courseware page
    When I press the "subsection" delete icon
    And I confirm the alert
    Then the subsection does not exist
