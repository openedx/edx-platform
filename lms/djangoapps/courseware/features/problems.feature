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
        | radio_text        |
        | checkbox_text     |

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
        | radio_text        |
        | checkbox_text     |

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
        | radio_text        |
        | checkbox_text     |


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
        | radio_text        | correct       |
        | radio_text        | incorrect     |
        | checkbox_text     | correct       |
        | checkbox_text     | incorrect     |


    Scenario: I can answer a problem with one attempt correctly and not reset
        Given I am viewing a "multiple choice" problem with "1" attempt
        When I answer a "multiple choice" problem "correctly"
        Then The "Reset" button does not appear

    Scenario: I can answer a problem with multiple attempts correctly and still reset the problem
        Given I am viewing a "multiple choice" problem with "3" attempts
        Then I should see "You have used 0 of 3 submissions" somewhere in the page
        When I answer a "multiple choice" problem "correctly"
        Then The "Reset" button does appear

    Scenario: I can view how many attempts I have left on a problem
        Given I am viewing a "multiple choice" problem with "3" attempts
        Then I should see "You have used 0 of 3 submissions" somewhere in the page
        When I answer a "multiple choice" problem "incorrectly"
        And I reset the problem
        Then I should see "You have used 1 of 3 submissions" somewhere in the page
        When I answer a "multiple choice" problem "incorrectly"
        And I reset the problem
        Then I should see "You have used 2 of 3 submissions" somewhere in the page
        And The "Final Check" button does appear
        When I answer a "multiple choice" problem "correctly"
        Then The "Reset" button does not appear

    Scenario: I can view and hide the answer if the problem has it:
        Given I am viewing a "numerical" that shows the answer "always"
        When I press the button with the label "Show Answer(s)"
        Then the button with the label "Hide Answer(s)" does appear
        And the button with the label "Show Answer(s)" does not appear
        And I should see "4.14159" somewhere in the page
        When I press the button with the label "Hide Answer(s)"
        Then the button with the label "Show Answer(s)" does appear
        And I should not see "4.14159" anywhere on the page
    
    Scenario: I can see my score on a problem when I answer it and after I reset it
        Given I am viewing a "<ProblemType>" problem
        When I answer a "<ProblemType>" problem "<Correctness>ly"
        Then I should see a score of "<Score>"
        When I reset the problem
        Then I should see a score of "<Points Possible>"

        Examples:
        | ProblemType       | Correctness   | Score               | Points Possible    |
        | drop down         | correct       | 1/1 points          | 1 point possible   |
        | drop down         | incorrect     | 1 point possible    | 1 point possible   |
        | multiple choice   | correct       | 1/1 points          | 1 point possible   |
        | multiple choice   | incorrect     | 1 point possible    | 1 point possible   |
        | checkbox          | correct       | 1/1 points          | 1 point possible   |
        | checkbox          | incorrect     | 1 point possible    | 1 point possible   |
        | radio             | correct       | 1/1 points          | 1 point possible   |
        | radio             | incorrect     | 1 point possible    | 1 point possible   |
        | string            | correct       | 1/1 points          | 1 point possible   |
        | string            | incorrect     | 1 point possible    | 1 point possible   |
        | numerical         | correct       | 1/1 points          | 1 point possible   |
        | numerical         | incorrect     | 1 point possible    | 1 point possible   |
        | formula           | correct       | 1/1 points          | 1 point possible   |
        | formula           | incorrect     | 1 point possible    | 1 point possible   |
        | script            | correct       | 2/2 points          | 2 points possible  |
        | script            | incorrect     | 2 points possible   | 2 points possible  |

    Scenario: I can see my score on a problem to which I submit a blank answer
        Given I am viewing a "<ProblemType>" problem
        When I check a problem
        Then I should see a score of "<Points Possible>"

        Examples:
        | ProblemType       | Points Possible    |
        | drop down         | 1 point possible   |
        | multiple choice   | 1 point possible   |
        | checkbox          | 1 point possible   |
        | radio             | 1 point possible   |
        | string            | 1 point possible   |
        | numerical         | 1 point possible   |
        | formula           | 1 point possible   |
        | script            | 2 points possible  |
