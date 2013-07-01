Feature: Textbooks

  Scenario: No textbooks
    Given I have opened a new course in Studio
    When I go to the textbooks page
    Then I should see a message telling me to create a new textbook

  Scenario: Create a textbook
    Given I have opened a new course in Studio
    And I go to the textbooks page
    When I click on the New Textbook button
    And I name my textbook "Economics"
    And I name the first chapter "Chapter 1"
    And I click the Upload Asset link for the first chapter
    And I upload the textbook "textbook.pdf"
    And I wait for "2" seconds
    And I save the textbook
    Then I should see a textbook named "Economics" with a chapter path containing "/c4x/MITx/999/asset/textbook.pdf"
    And I reload the page
    Then I should see a textbook named "Economics" with a chapter path containing "/c4x/MITx/999/asset/textbook.pdf"
