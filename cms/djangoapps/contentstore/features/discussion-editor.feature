@shard_2
Feature: CMS.Discussion Component Editor
  As a course author, I want to be able to create discussion components.

  Scenario: User can view discussion component metadata
    Given I have created a Discussion Tag
    And I edit the component
    Then I see three alphabetized settings and their expected values

  # Safari doesn't save the name properly
  @skip_safari
  Scenario: User can modify display name
    Given I have created a Discussion Tag
    And I edit the component
    Then I can modify the display name
    And my display name change is persisted on save
