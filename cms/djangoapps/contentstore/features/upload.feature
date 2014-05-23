@shard_2
Feature: CMS.Upload Files
    As a course author, I want to be able to upload files for my students

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can upload files
        Given I am at the files and upload page of a Studio course
        When I upload the file "test" by clicking "Upload your first asset"
        Then I should see the file "test" was uploaded
        And The url for the file "test" is valid
        When I upload the file "test2"
        Then I should see the file "test2" was uploaded
        And The url for the file "test2" is valid

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can upload multiple files
        Given I am at the files and upload page of a Studio course
        When I upload the files "test,test2"
        Then I should see the file "test" was uploaded
        And I should see the file "test2" was uploaded
        And The url for the file "test2" is valid
        And The url for the file "test" is valid

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can update files
        Given I am at the files and upload page of a Studio course
        When I upload the file "test"
        And I upload the file "test"
        Then I should see only one "test"

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can delete uploaded files
        Given I am at the files and upload page of a Studio course
        When I upload the file "test"
        And I delete the file "test"
        Then I should not see the file "test" was uploaded
        And I see a confirmation that the file was deleted

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can download files
        Given I am at the files and upload page of a Studio course
        When I upload the file "test"
        Then I can download the correct "test" file

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can download updated files
        Given I am at the files and upload page of a Studio course
        When I upload the file "test"
        And I modify "test"
        And I reload the page
        And I upload the file "test"
        Then I can download the correct "test" file

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can lock assets through asset index
        Given I am at the files and upload page of a Studio course
        When I upload an asset
        And I lock the asset
        Then the asset is locked
        And I see a "saving" notification
        And I reload the page
        Then the asset is locked

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can unlock assets through asset index
        Given I have created a course with a locked asset
        When I unlock the asset
        Then the asset is unlocked
        And I see a "saving" notification
        And I reload the page
        Then the asset is unlocked

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Locked assets can't be viewed if logged in as an unregistered user
        Given I have created a course with a locked asset
        And the user "bob" exists
        When "bob" logs in
        Then the asset is protected

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Locked assets can be viewed if logged in as a registered user
        Given I have created a course with a locked asset
        And the user "bob" exists
        And the user "bob" is enrolled in the course
        When "bob" logs in
        Then the asset is viewable

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Locked assets can't be viewed if logged out
        Given I have created a course with a locked asset
        When I log out
        Then the asset is protected

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Locked assets can be viewed with is_staff account
        Given I have created a course with a locked asset
        And the user "staff" exists as a course is_staff
        When "staff" logs in
        Then the asset is viewable

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Unlocked assets can be viewed by anyone
        Given I have created a course with a unlocked asset
        When I log out
        Then the asset is viewable
