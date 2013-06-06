Feature: Navigate Course
    As a student in an edX course
    In order to view the course properly
    I want to be able to navigate through the content

    Scenario: I can navigate to a section
        Given I am viewing a course with multiple sections
        When I click on section "2"
        Then I should see the content of section "2"

    Scenario: I can navigate to subsections
        Given I am viewing a section with multiple subsections
        When I click on subsection "2"
        Then I should see the content of subsection "2"

    Scenario: I can navigate to sequences
        Given I am viewing a section with multiple sequences
        When I click on sequence "2"
        Then I should see the content of sequence "2"

    Scenario: I can go back to where I was after I log out and back in
        Given I am viewing a course with multiple sections
        When I click on section "2"
        And I return later
        Then I should see that I was most recently in section "2"
