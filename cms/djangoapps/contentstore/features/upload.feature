@shard_3
Feature: CMS.Upload Files
    As a course author, I want to be able to upload files for my students

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can upload files
        Given I have opened a new course in Studio
        And I go to the files and uploads page
        When I upload the file "test"
        Then I should see the file "test" was uploaded
        And The url for the file "test" is valid

    @skip_safari
    Scenario: Users can upload multiple files
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the files "test","test2"
        Then I should see the file "test" was uploaded
        And I should see the file "test2" was uploaded
        And The url for the file "test2" is valid
        And The url for the file "test" is valid

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can update files
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the file "test"
        And I upload the file "test"
        Then I should see only one "test"

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can delete uploaded files
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the file "test"
        And I delete the file "test"
        Then I should not see the file "test" was uploaded
        And I see a confirmation that the file was deleted

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can download files
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the file "test"
        Then I can download the correct "test" file

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can download updated files
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the file "test"
        And I modify "test"
        And I reload the page
        And I upload the file "test"
        Then I can download the correct "test" file

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can lock assets through asset index
        Given I have opened a new course in studio
        And I go to the files and uploads page
        When I upload the file "test"
        And I lock "test"
        Then "test" is locked
        And I see a "saving" notification
        And I reload the page
        Then "test" is locked

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Users can unlock assets through asset index
        Given I have opened a course with a locked asset "test"
        And I unlock "test"
        Then "test" is unlocked
        And I see a "saving" notification
        And I reload the page
        Then "test" is unlocked

    # Uploading isn't working on safari with sauce labs
    # TODO: work with Jay
#    @skip_safari
#    Scenario: Locked assets can't be viewed if logged in as unregistered user
#        Given I have opened a course with a locked asset "locked.html"
#        Then the asset "locked.html" can be clicked from the asset index
#        And the user "bob" exists
#        And "bob" logs in
#        Then the asset "locked.html" is protected

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Locked assets can't be viewed if logged out
        Given I have opened a course with a locked asset "locked.html"
        # Note that logging out doesn't really matter at the moment-
        # the asset will be protected because the user sent to middleware is the anonymous user.
        # Need to work with Jay.
        And I log out
        Then the asset "locked.html" is protected

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Locked assets can be viewed with is_staff account
        Given I have opened a course with a locked asset "locked.html"
        And the user "staff" exists as a course is_staff
        And "staff" logs in
        Then the asset "locked.html" can be clicked from the asset index

    # Uploading isn't working on safari with sauce labs
    @skip_safari
    Scenario: Unlocked assets can be viewed by anyone
        Given I have opened a course with a unlocked asset "unlocked.html"
        Then the asset "unlocked.html" is viewable
        And the user "bob" exists
        And "bob" logs in
        Then the asset "unlocked.html" is viewable
        And I log out
        Then the asset "unlocked.html" is viewable
