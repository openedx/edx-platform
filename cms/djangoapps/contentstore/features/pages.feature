@shard_2
Feature: CMS.Pages
    As a course author, I want to be able to add pages

    Scenario: Users can add static pages
        Given I have opened the pages page in a new course
        Then I should not see any static pages
        When I add a new static page
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
        When I drag the first static page to the last
        Then the static pages are switched
        And I reload the page
        Then the static pages are switched

    Scenario: Users can reorder built-in pages
        Given I have opened the pages page in a new course
        Then the built-in pages are in the default order
        When I drag the first page to the last
        Then the built-in pages are switched
        And I reload the page
        Then the built-in pages are switched

    Scenario: Users can reorder built-in pages amongst static pages
        Given I have created two different static pages
        Then the pages are in the default order
        When I drag the first page to the last
        Then the pages are switched
        And I reload the page
        Then the pages are switched

    Scenario: Users can toggle visibility on hideable pages
        Given I have opened the pages page in a new course
        Then I should see the "wiki" page as "visible"
        When I toggle the visibility of the "wiki" page
        Then I should see the "wiki" page as "hidden"
        And I reload the page
        Then I should see the "wiki" page as "hidden"
        When I toggle the visibility of the "wiki" page
        Then I should see the "wiki" page as "visible"
        And I reload the page
        Then I should see the "wiki" page as "visible"

