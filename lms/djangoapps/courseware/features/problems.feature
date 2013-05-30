Feature: Answer problems
    As a student in an edX course
    In order to test my understanding of the material
    I want to answer problems

    Scenario: I can answer a problem correctly
        Given External graders respond "correct"
        And I am viewing a "<ProblemType>" problem
        When I answer a "<ProblemType>" problem "correctly"
        Then My "<ProblemType>" answer is marked "correct"
        And The "<ProblemType>" problem displays a "correct" answer

        Examples:
        | ProblemType       |
        | drop down         |
        | multiple choice   |
        | checkbox          |
        | radio             |
        | string            |
        | numerical         |
        | formula           |
        | script            |
        | code              |

    Scenario: I can answer a problem incorrectly
        Given External graders respond "incorrect"
        And I am viewing a "<ProblemType>" problem
        When I answer a "<ProblemType>" problem "incorrectly"
        Then My "<ProblemType>" answer is marked "incorrect"
        And The "<ProblemType>" problem displays a "incorrect" answer

        Examples:
        | ProblemType       |
        | drop down         |
        | multiple choice   |
        | checkbox          |
        | radio             |
        | string            |
        | numerical         |
        | formula           |
        | script            |
        | code              |

    Scenario: I can submit a blank answer
        Given I am viewing a "<ProblemType>" problem
        When I check a problem
        Then My "<ProblemType>" answer is marked "incorrect"
        And The "<ProblemType>" problem displays a "blank" answer

        Examples:
        | ProblemType       |
        | drop down         |
        | multiple choice   |
        | checkbox          |
        | radio             |
        | string            |
        | numerical         |
        | formula           |
        | script            |


    Scenario: I can reset a problem
        Given I am viewing a "<ProblemType>" problem
        And I answer a "<ProblemType>" problem "<Correctness>ly"
        When I reset the problem
        Then My "<ProblemType>" answer is marked "unanswered"
        And The "<ProblemType>" problem displays a "blank" answer

        Examples:
        | ProblemType       | Correctness   |
        | drop down         | correct       |
        | drop down         | incorrect     |
        | multiple choice   | correct       |
        | multiple choice   | incorrect     |
        | checkbox          | correct       |
        | checkbox          | incorrect     |
        | radio             | correct       |
        | radio             | incorrect     |
        | string            | correct       |
        | string            | incorrect     |
        | numerical         | correct       |
        | numerical         | incorrect     |
        | formula           | correct       |
        | formula           | incorrect     |
        | script            | correct       |
        | script            | incorrect     |


    Scenario: I can answer a problem with one attempt correctly
        Given I am viewing a "multiple choice" problem with "1" attempt
        Then I should see "You have used 0 of 1 submissions" somewhere in the page
        And The "Final Check" button does appear
        When I answer a "multiple choice" problem "correctly"
        Then My "multiple choice" answer is marked "correct"
        And The "multiple choice" problem displays a "correct" answer
        And The "Reset" button does not appear

    Scenario: I can answer a problem with one attempt incorrectly
        Given I am viewing a "multiple choice" problem with "1" attempt
        When I answer a "multiple choice" problem "incorrectly"
        Then My "multiple choice" answer is marked "incorrect"
        And The "multiple choice" problem displays a "incorrect" answer
        And The "Reset" button does not appear

    Scenario: I can answer a problem with multiple attempts correctly
        Given I am viewing a "multiple choice" problem with "3" attempts
        Then I should see "You have used 0 of 3 submissions" somewhere in the page
        When I answer a "multiple choice" problem "correctly"
        Then My "multiple choice" answer is marked "correct"
        And The "multiple choice" problem displays a "correct" answer
        And The "Reset" button does appear

    Scenario: I can answer a problem with multiple attempts correctly on final guess
        Given I am viewing a "multiple choice" problem with "3" attempts
        Then I should see "You have used 0 of 3 submissions" somewhere in the page
        When I answer a "multiple choice" problem "incorrectly"
        Then My "multiple choice" answer is marked "incorrect"
        And The "multiple choice" problem displays a "incorrect" answer
        When I reset the problem
        Then I should see "You have used 1 of 3 submissions" somewhere in the page
        When I answer a "multiple choice" problem "incorrectly"
        Then My "multiple choice" answer is marked "incorrect"
        And The "multiple choice" problem displays a "incorrect" answer
        When I reset the problem
        Then I should see "You have used 2 of 3 submissions" somewhere in the page
        And The "Final Check" button does appear
        When I answer a "multiple choice" problem "correctly"
        Then My "multiple choice" answer is marked "correct"
        And The "multiple choice" problem displays a "correct" answer
        And The "Reset" button does not appear

    Scenario: I can view and hide the answer if the problem has it:
        Given I am viewing a "numerical" that shows the answer "always"
        Then The "Show Answer" button does appear
        When I press the "Show Answer" button
        Then The "Hide Answer" button does appear
        And The "Show Answer" button does not appear
        And I should see "4.14159" somewhere in the page
        When I press the "Hide Answer" button
        Then The "Show Answer" button does appear
        And I do not see "4.14159" anywhere on the page
