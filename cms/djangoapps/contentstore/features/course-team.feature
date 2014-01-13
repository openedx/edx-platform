@shard_2
Feature: CMS.Course Team
    As a course author, I want to be able to add others to my team

    Scenario: Admins can add other users
        Given I have opened a new course in Studio
        And the user "alice" exists
        And I am viewing the course team settings
        When I add "alice" to the course team
        And "alice" logs in
        Then she does see the course on her page

    Scenario: Added admins cannot delete or add other users
        Given I have opened a new course in Studio
        And the user "bob" exists
        And I am viewing the course team settings
        When I add "bob" to the course team
        And "bob" logs in
        And he selects the new course
        And he views the course team settings
        Then he cannot delete users
        And he cannot add users

    Scenario: Admins can delete other users
        Given I have opened a new course in Studio
        And the user "carol" exists
        And I am viewing the course team settings
        When I add "carol" to the course team
        And I delete "carol" from the course team
        And "carol" logs in
        Then she does not see the course on her page

    Scenario: Admins cannot add users that do not exist
        Given I have opened a new course in Studio
        And I am viewing the course team settings
        When I add "dennis" to the course team
        Then I should see "Could not find user by email address" somewhere on the page

    Scenario: Admins should be able to make other people into admins
        Given I have opened a new course in Studio
        And the user "emily" exists
        And I am viewing the course team settings
        And I add "emily" to the course team
        When I make "emily" a course team admin
        And "emily" logs in
        And she selects the new course
        And she views the course team settings
        Then "emily" should be marked as an admin
        And she can add users
        And she can delete users

    Scenario: Admins should be able to remove other admins
        Given I have opened a new course in Studio
        And the user "frank" exists as a course admin
        And I am viewing the course team settings
        When I remove admin rights from "frank"
        And "frank" logs in
        And he selects the new course
        And he views the course team settings
        Then "frank" should not be marked as an admin
        And he cannot add users
        And he cannot delete users

    # Disabled 1/13/14 due to flakiness observed in master
    #Scenario: Admins should be able to give course ownership to someone else
    #    Given I have opened a new course in Studio
    #    And the user "gina" exists
    #    And I am viewing the course team settings
    #    When I add "gina" to the course team
    #    And I make "gina" a course team admin
    #    And I remove admin rights from myself
    #    And "gina" logs in
    #    And she selects the new course
    #    And she views the course team settings
    #    And she deletes me from the course team
    #    And I am logged into studio
    #    Then I do not see the course on my page

    Scenario: Admins should be able to remove their own admin rights
        Given I have opened a new course in Studio
        And the user "harry" exists as a course admin
        And I am viewing the course team settings
        Then I should be marked as an admin
        And I can add users
        And I can delete users
        When I remove admin rights from myself
        Then I should not be marked as an admin
        And I cannot add users
        And I cannot delete users
        And I cannot make myself a course team admin
