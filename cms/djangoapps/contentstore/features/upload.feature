Feature: Upload Files
    As a course author, I want to be able to upload files for my students

    Scenario: Users can upload files
        Given I have opened a new course in Studio
        And I go to the files and uploads page
        When I upload the file "upload.feature"
        Then I see the file "upload.feature" was uploaded

    Scenario: Users can update files
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the file "upload.feature"
        And I upload the file "upload.feature"
        Then I see only one "upload.feature"
