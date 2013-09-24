@shard_3
Feature: CMS.HTML Editor
  As a course author, I want to be able to create HTML blocks.

  Scenario: User can view metadata
    Given I have created a Blank HTML Page
    And I edit and select Settings
    Then I see only the HTML display name setting

  # Safari doesn't save the name properly
  @skip_safari
  Scenario: User can modify display name
    Given I have created a Blank HTML Page
    And I edit and select Settings
    Then I can modify the display name
    And my display name change is persisted on save

  Scenario: Edit High Level source is available for LaTeX html
    Given I have created an E-text Written in LaTeX
    When I edit and select Settings
    Then Edit High Level Source is visible
