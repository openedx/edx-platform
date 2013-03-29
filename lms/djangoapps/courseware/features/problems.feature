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
        | string            | correct       |
        | string            | incorrect     |
        | numerical         | correct       |
        | numerical         | incorrect     |
        | formula           | correct       |
        | formula           | incorrect     |
        | script            | correct       |
        | script            | incorrect     |
