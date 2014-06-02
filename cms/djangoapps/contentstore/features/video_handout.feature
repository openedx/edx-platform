@shard_3 @requires_stub_youtube
Feature: CMS Video Component Handout
  As a course author, I want to be able to create video handout

  # 1
  Scenario: Handout uploading works correctly
    Given I have created a Video component with handout file "textbook.pdf"
    And I save changes
    Then I can see video button "handout"
    And I can download handout file with mime type "application/pdf"

  # 2
  Scenario: Handout downloading works correctly w/ preliminary saving
    Given I have created a Video component with handout file "textbook.pdf"
    And I save changes
    And I edit the component
    And I open tab "Advanced"
    And I can download handout file in editor with mime type "application/pdf"

  # 3
  Scenario: Handout downloading works correctly w/o preliminary saving
    Given I have created a Video component with handout file "textbook.pdf"
    And I can download handout file in editor with mime type "application/pdf"

  # 4
  Scenario: Handout clearing works correctly w/ preliminary saving
    Given I have created a Video component with handout file "textbook.pdf"
    And I save changes
    And I can download handout file with mime type "application/pdf"
    And I edit the component
    And I open tab "Advanced"
    And I clear handout
    And I save changes
    Then I do not see video button "handout"

  # 5
  Scenario: Handout clearing works correctly w/o preliminary saving
    Given I have created a Video component with handout file "asset.html"
    And I clear handout
    And I save changes
    Then I do not see video button "handout"

  # 6
  Scenario: User can easy replace the handout by another one w/ preliminary saving
    Given I have created a Video component with handout file "asset.html"
    And I save changes
    Then I can see video button "handout"
    And I can download handout file with mime type "text/html"
    And I edit the component
    And I open tab "Advanced"
    And I replace handout file by "textbook.pdf"
    And I save changes
    Then I can see video button "handout"
    And I can download handout file with mime type "application/pdf"

  # 7
  Scenario: User can easy replace the handout by another one w/o preliminary saving
    Given I have created a Video component with handout file "asset.html"
    And I replace handout file by "textbook.pdf"
    And I save changes
    Then I can see video button "handout"
    And I can download handout file with mime type "application/pdf"

  # 8
  Scenario: Upload file "A" -> Remove it -> Upload file "B"
    Given I have created a Video component with handout file "asset.html"
    And I clear handout
    And I upload handout file "textbook.pdf"
    And I save changes
    Then I can see video button "handout"
    And I can download handout file with mime type "application/pdf"
