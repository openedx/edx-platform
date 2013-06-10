Feature: Course Team
    As a course author, I want to be able to add others to my team

    Scenario: Users can add other users
        Given I have opened a new course in Studio
        And The user "abcd" exists
        And I am viewing the course team settings
        When I add "abcd" to the course team
        And "abcd" logs in
        Then He does see the course on his page

    Scenario: Added users cannot delete or add other users
        Given I have opened a new course in Studio
        And The user "abcd" exists
        And I am viewing the course team settings
        When I add "abcd" to the course team
        And "abcd" logs in
        Then He cannot delete users
        And He cannot add users

    Scenario: Users can delete other users
        Given I have opened a new course in Studio
        And The user "abcd" exists
        And I am viewing the course team settings
        When I add "abcd" to the course team
        And I delete "abcd" from the course team
        And "abcd" logs in
        Then He does not see the course on his page

    Scenario: Users cannot add users that do not exist
        Given I have opened a new course in Studio
        And I am viewing the course team settings
        When I add "abcd" to the course team
        Then I should see "Could not find user by email address" somewhere on the page
