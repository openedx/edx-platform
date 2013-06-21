Feature: Upload Files
    As a course author, I want to be able to upload files for my students

    Scenario: Users can upload files
        Given I have opened a new course in Studio
        And I go to the files and uploads page
        When I upload the file "test"
        Then I should see the file "test" was uploaded
        And The url for the file "test" is valid

    Scenario: Users can update files
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the file "test"
        And I upload the file "test"
        Then I should see only one "test"

    Scenario: Users can delete uploaded files
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the file "test"
        And I delete the file "test"
        Then I should not see the file "test" was uploaded

    Scenario: Users can download files
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the file "test"
        Then I can download the correct "test" file

    Scenario: Users can download updated files
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the file "test"
        And I modify "test"
        And I reload the page
        And I upload the file "test"
        Then I can download the correct "test" file
