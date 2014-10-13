@shard_1
Feature: CMS.Course Outline
    In order to quickly view the details of a course's section and set release dates and grading
    As a course author
    I want to use the course outline page

    Scenario: The default layout for the outline page is to show sections in expanded view
        Given I have a course with multiple sections
        When I navigate to the course outline page
        Then I see the "Collapse All Sections" link
        And all sections are expanded

    Scenario: Expand /collapse for a course with no sections
        Given I have a course with no sections
        When I navigate to the course outline page
        Then I do not see the "Collapse All Sections" link

    Scenario: Collapse link appears after creating first section of a course
        Given I have a course with no sections
        When I navigate to the course outline page
        And I add a section
        Then I see the "Collapse All Sections" link
        And all sections are expanded

    Scenario: Collapse link is removed after last section of a course is deleted
        Given I have a course with 1 section
        And I navigate to the course outline page
        And I press the section delete icon
        When I will confirm all alerts
        Then I do not see the "Collapse All Sections" link

    Scenario: Collapsing all sections when all sections are expanded
        Given I navigate to the outline page of a course with multiple sections
        And all sections are expanded
        When I click the "Collapse All Sections" link
        Then I see the "Expand All Sections" link
        And all sections are collapsed

    Scenario: Collapsing all sections when 1 or more sections are already collapsed
        Given I navigate to the outline page of a course with multiple sections
        And all sections are expanded
        When I collapse the first section
        And I click the "Collapse All Sections" link
        Then I see the "Expand All Sections" link
        And all sections are collapsed

    Scenario: Expanding all sections when all sections are collapsed
        Given I navigate to the outline page of a course with multiple sections
        And I click the "Collapse All Sections" link
        When I click the "Expand All Sections" link
        Then I see the "Collapse All Sections" link
        And all sections are expanded

    Scenario: Expanding all sections when 1 or more sections are already expanded
        Given I navigate to the outline page of a course with multiple sections
        And I click the "Collapse All Sections" link
        When I expand the first section
        And I click the "Expand All Sections" link
        Then I see the "Collapse All Sections" link
        And all sections are expanded
