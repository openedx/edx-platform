Feature: Answer choice problems
    As a student in an edX course
    In order to test my understanding of the material
    I want to answer choice based problems

    Scenario: I can answer a problem correctly
        Given I am viewing a "<ProblemType>" problem
        When I answer a "<ProblemType>" problem "correctly"
        Then My "<ProblemType>" answer is marked "correct"

        Examples:
        | ProblemType       |
        | drop down         |
        | multiple choice   |
        | checkbox          |
        | string            |
        | numerical         |
        | formula           |
        | script            |

    Scenario: I can answer a problem incorrectly
        Given I am viewing a "<ProblemType>" problem
        When I answer a "<ProblemType>" problem "incorrectly"
        Then My "<ProblemType>" answer is marked "incorrect"

        Examples:
        | ProblemType       |
        | drop down         |
        | multiple choice   |
        | checkbox          |
        | string            |
        | numerical         |
        | formula           |
        | script            |

    Scenario: I can submit a blank answer
        Given I am viewing a "<ProblemType>" problem
        When I check a problem 
        Then My "<ProblemType>" answer is marked "incorrect"

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
