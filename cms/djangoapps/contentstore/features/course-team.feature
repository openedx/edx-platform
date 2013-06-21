Feature: Course Team
    As a course author, I want to be able to add others to my team

    Scenario: Users can add other users
        Given I have opened a new course in Studio
        And the user "alice" exists
        And I am viewing the course team settings
        When I add "alice" to the course team
        And "alice" logs in
        Then she does see the course on her page

    Scenario: Added users cannot delete or add other users
        Given I have opened a new course in Studio
        And the user "bob" exists
        And I am viewing the course team settings
        When I add "bob" to the course team
        And "bob" logs in
        Then he cannot delete users
        And he cannot add users

    Scenario: Users can delete other users
        Given I have opened a new course in Studio
        And the user "carol" exists
        And I am viewing the course team settings
        When I add "carol" to the course team
        And I delete "carol" from the course team
        And "carol" logs in
        Then she does not see the course on her page

    Scenario: Users cannot add users that do not exist
        Given I have opened a new course in Studio
        And I am viewing the course team settings
        When I add "dennis" to the course team
        Then I should see "Could not find user by email address" somewhere on the page
