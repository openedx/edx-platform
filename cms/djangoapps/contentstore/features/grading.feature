Feature: Course Grading
    As a course author, I want to be able to configure how my course is graded

    Scenario: Users can add grading ranges
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I add "1" new grade
        Then I see I now have "3" grades

    Scenario: Users can only have up to 5 grading ranges
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I add "6" new grades
        Then I see I now have "5" grades

    #Cannot reliably make the delete button appear so using javascript instead
    Scenario: Users can delete grading ranges
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I add "1" new grade
        And I delete a grade
        Then I see I now have "2" grades

    Scenario: Users can move grading ranges
        Given I have opened a new course in Studio
        And I am viewing the grading settings
        When I move a grading section
        Then I see that the grade range has changed

    Scenario: Users can modify Assignment types
        Given I have opened a new course in Studio
        And I have populated the course
        And I am viewing the grading settings
        When I change assignment type "Homework" to "New Type"
        And I go back to the main course page
        Then I do see the assignment name "New Type"
        And I do not see the assignment name "Homework"

    Scenario: Users can delete Assignment types
        Given I have opened a new course in Studio
        And I have populated the course
        And I am viewing the grading settings
        When I delete the assignment type "Homework"
        And I go back to the main course page
        Then I do not see the assignment name "Homework"

    Scenario: Users can add Assignment types
        Given I have opened a new course in Studio
        And I have populated the course
        And I am viewing the grading settings
        When I add a new assignment type "New Type"
        And I go back to the main course page
        Then I do see the assignment name "New Type"
