Feature: Video Component Editor
  As a course author, I want to be able to create video components.

  #Sauce Labs cannot delete cookies

  Scenario: User can view Video metadata
    Given I have created a Video component
    And I edit the component
    Then I see the correct video settings and default values

  Scenario: User can modify Video display name
    Given I have created a Video component
    And I edit the component
    Then I can modify the display name
    And my video display name change is persisted on save

  @Sauce
  Scenario: Captions are hidden when "show captions" is false
    Given I have created a Video component
    And I have set "show captions" to False
    Then when I view the video it does not show the captions

  @Sauce
  Scenario: Captions are shown when "show captions" is true
    Given I have created a Video component
    And I have set "show captions" to True
    Then when I view the video it does show the captions
