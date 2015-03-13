@shard_2
Feature: CMS.Textbooks

  Scenario: No textbooks
    Given I have opened a new course in Studio
    When I go to the textbooks page
    Then I should see a message telling me to create a new textbook

# Flaky test, disabled 03/13/2015. TNL-1679.
#  Scenario: Create a textbook
#    Given I have opened a new course in Studio
#    And I go to the textbooks page
#    When I click on the New Textbook button
#    And I name my textbook "Economics"
#    And I name the first chapter "Chapter 1"
#    And I click the Upload Asset link for the first chapter
#    And I upload the textbook "textbook.pdf"
#    And I save the textbook
#    Then I should see a textbook named "Economics" with a chapter path containing "/static/textbook.pdf"
#    And I reload the page
#    Then I should see a textbook named "Economics" with a chapter path containing "/static/textbook.pdf"

  Scenario: Create a textbook with multiple chapters
    Given I have opened a new course in Studio
    And I go to the textbooks page
    When I click on the New Textbook button
    And I name my textbook "History"
    And I name the first chapter "Britain"
    And I type in "britain.pdf" for the first chapter asset
    And I click Add a Chapter
    And I name the second chapter "America"
    And I type in "america.pdf" for the second chapter asset
    And I save the textbook
    Then I should see a textbook named "History" with 2 chapters
    And I click the textbook chapters
    Then I should see a textbook named "History" with 2 chapters
    And the first chapter should be named "Britain"
    And the first chapter should have an asset called "britain.pdf"
    And the second chapter should be named "America"
    And the second chapter should have an asset called "america.pdf"
    And I reload the page
    Then I should see a textbook named "History" with 2 chapters
    And I click the textbook chapters
    Then I should see a textbook named "History" with 2 chapters
    And the first chapter should be named "Britain"
    And the first chapter should have an asset called "britain.pdf"
    And the second chapter should be named "America"
    And the second chapter should have an asset called "america.pdf"
