@shard_2
Feature: CMS.Static Pages
    As a course author, I want to be able to add static pages

    Scenario: Users can add static pages
        Given I have opened a new course in Studio
        And I go to the static pages page
        Then I should not see any static pages
        When I add a new page
        Then I should see a static page named "Empty"

    Scenario: Users can delete static pages
        Given I have created a static page
        When I "delete" the static page
        Then I am shown a prompt
        When I confirm the prompt
        Then I should not see any static pages

    # Safari won't update the name properly
    @skip_safari
    Scenario: Users can edit static pages
        Given I have created a static page
        When I "edit" the static page
        And I change the name to "New"
        Then I should see a static page named "New"

    # Safari won't update the name properly
    @skip_safari
    Scenario: Users can reorder static pages
        Given I have created two different static pages
        When I reorder the tabs
        Then the tabs are in the reverse order
        And I reload the page
        Then the tabs are in the reverse order
