@shard_1
Feature: CMS.Course checklists

  Scenario: A course author sees checklists defined by edX
    Given I have opened a new course in Studio
    When I select Checklists from the Tools menu
    Then I see the four default edX checklists

  Scenario: A course author can mark tasks as complete
    Given I have opened Checklists
    Then I can check and uncheck tasks in a checklist
    And I reload the page
    Then the tasks are correctly selected

  # There are issues getting link to be active in browsers other than chrome
  @skip_firefox
  @skip_internetexplorer
  @skip_safari
  Scenario: A task can link to a location within Studio
    Given I have opened Checklists
    When I select a link to the course outline
    Then I am brought to the course outline page
    And I press the browser back button
    Then I am brought back to the course outline in the correct state

  # There are issues getting link to be active in browsers other than chrome
  @skip_firefox
  @skip_internetexplorer
  @skip_safari
  Scenario: A task can link to a location outside Studio
    Given I have opened Checklists
    When I select a link to help page
    Then I am brought to the help page in a new window
