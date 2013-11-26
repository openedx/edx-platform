@shard_1
Feature: LMS.Navigate Course
    As a student in an edX course
    In order to access courseware
    I want to be able to navigate through the content

    Scenario: I can navigate to a section
        Given I am viewing a course with multiple sections
        When I navigate to a section
        Then I see the content of the section

    Scenario: I can navigate to subsections
        Given I am viewing a section with multiple subsections
        When I navigate to a subsection
        Then I see the content of the subsection

    Scenario: I can navigate to sequences
        Given I am viewing a section with multiple sequences
        When I navigate to an item in a sequence
        Then I see the content of the sequence item
        And a "seq_goto" browser event is emitted

    Scenario: I can return to the last section I visited
       Given I am viewing a course with multiple sections
       When I navigate to a section
        And I see the content of the section
        And I return to the courseware
        Then I see that I was most recently in the subsection
