Feature: Course checklists

  Scenario: A course author sees checklists defined by edX
    Given I have opened a new course in Studio
    When I select Checklists from the Tools menu
    Then I see the four default edX checklists

  Scenario: A course author can mark tasks as complete
    Given I have opened a new course in Studio
    When I select Checklists from the Tools menu
    Then I can check and uncheck tasks in a checklist
    And They are correctly selected after I reload the page