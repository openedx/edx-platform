@shard_1 @requires_stub_xqueue
Feature: LMS.Answer problems
    As a student in an edX course
    In order to test my understanding of the material
    I want to answer problems

    Scenario: I can reset a problem
        Given I am viewing a randomization "<Randomization>" "<ProblemType>" problem with reset button on
        And I answer a "<ProblemType>" problem "<Correctness>ly"
        When I reset the problem
        Then my "<ProblemType>" answer is marked "unanswered"
        And The "<ProblemType>" problem displays a "blank" answer

        Examples:
        | ProblemType       | Correctness   | Randomization |
        | drop down         | correct       | always        |
        | drop down         | incorrect     | always        |
        | multiple choice   | correct       | always        |
        | multiple choice   | incorrect     | always        |
        | checkbox          | correct       | always        |
        | checkbox          | incorrect     | always        |
        | radio             | correct       | always        |
        | radio             | incorrect     | always        |
        #| string            | correct       | always        |
        #| string            | incorrect     | always        |
        | numerical         | correct       | always        |
        | numerical         | incorrect     | always        |
        | formula           | correct       | always        |
        | formula           | incorrect     | always        |
        | script            | correct       | always        |
        | script            | incorrect     | always        |
        | radio_text        | correct       | always        |
        | radio_text        | incorrect     | always        |
        | checkbox_text     | correct       | always        |
        | checkbox_text     | incorrect     | always        |
        | image             | correct       | always        |
        | image             | incorrect     | always        |

    Scenario: I can reset a non-randomized problem that I answer incorrectly
        Given I am viewing a randomization "<Randomization>" "<ProblemType>" problem with reset button on
        And I answer a "<ProblemType>" problem "<Correctness>ly"
        When I reset the problem
        Then my "<ProblemType>" answer is marked "unanswered"
        And The "<ProblemType>" problem displays a "blank" answer

        Examples:
        | ProblemType       | Correctness   | Randomization   |
        | drop down         | incorrect     | never           |
        | multiple choice   | incorrect     | never           |
        | checkbox          | incorrect     | never           |
        # TE-572
        #| radio             | incorrect     | never           |
        #| string            | incorrect     | never           |
        | numerical         | incorrect     | never           |
        | formula           | incorrect     | never           |
        # TE-572 failing intermittently
        #| script            | incorrect     | never           |
        | radio_text        | incorrect     | never           |
        | checkbox_text     | incorrect     | never           |
        | image             | incorrect     | never           |

    Scenario: The reset button doesn't show up
        Given I am viewing a randomization "<Randomization>" "<ProblemType>" problem with reset button on
        And I answer a "<ProblemType>" problem "<Correctness>ly"
        Then The "Reset" button does not appear

        Examples:
        | ProblemType       | Correctness   | Randomization   |
        | drop down         | correct       | never           |
        | multiple choice   | correct       | never           |
        | checkbox          | correct       | never           |
        | radio             | correct       | never           |
        #| string            | correct       | never           |
        | numerical         | correct       | never           |
        | formula           | correct       | never           |
        | script            | correct       | never           |
        | radio_text        | correct       | never           |
        | checkbox_text     | correct       | never           |
        | image             | correct       | never           |

    Scenario: I can answer a problem with one attempt correctly and not reset
        Given I am viewing a "multiple choice" problem with "1" attempt
        When I answer a "multiple choice" problem "correctly"
        Then The "Reset" button does not appear

    Scenario: I can answer a problem with multiple attempts correctly and still reset the problem
        Given I am viewing a "multiple choice" problem with "3" attempts
        Then I should see "You have used 0 of 3 submissions" somewhere in the page
        When I answer a "multiple choice" problem "correctly"
        Then The "Reset" button does appear

    Scenario: I can answer a problem with multiple attempts correctly but cannot reset because randomization is off
        Given I am viewing a randomization "never" "multiple choice" problem with "3" attempts with reset
        Then I should see "You have used 0 of 3 submissions" somewhere in the page
        When I answer a "multiple choice" problem "correctly"
        Then The "Reset" button does not appear

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
        When I press the button with the label "SHOW ANSWER"
        Then the Show/Hide button label is "HIDE ANSWER"
        And I should see "4.14159" somewhere in the page
        When I press the button with the label "HIDE ANSWER"
        Then the Show/Hide button label is "SHOW ANSWER"
        And I should not see "4.14159" anywhere on the page

    Scenario: I can see my score on a problem when I answer it and after I reset it
        Given I am viewing a "<ProblemType>" problem
        When I answer a "<ProblemType>" problem "<Correctness>ly"
        Then I should see a score of "<Score>"
        When I reset the problem
        Then I should see a score of "<Points Possible>"

        Examples:
        | ProblemType       | Correctness   | Score               | Points Possible    |
        | drop down         | correct       | 1/1 point           | 1 point possible   |
        | drop down         | incorrect     | 1 point possible    | 1 point possible   |
        | multiple choice   | correct       | 1/1 point           | 1 point possible   |
        | multiple choice   | incorrect     | 1 point possible    | 1 point possible   |
        | checkbox          | correct       | 1/1 point           | 1 point possible   |
        | checkbox          | incorrect     | 1 point possible    | 1 point possible   |
        | radio             | correct       | 1/1 point           | 1 point possible   |
        | radio             | incorrect     | 1 point possible    | 1 point possible   |
        #| string            | correct       | 1/1 point           | 1 point possible   |
        #| string            | incorrect     | 1 point possible    | 1 point possible   |
        | numerical         | correct       | 1/1 point           | 1 point possible   |
        | numerical         | incorrect     | 1 point possible    | 1 point possible   |
        | formula           | correct       | 1/1 point           | 1 point possible   |
        | formula           | incorrect     | 1 point possible    | 1 point possible   |
        | script            | correct       | 2/2 points          | 2 points possible  |
        | script            | incorrect     | 2 points possible   | 2 points possible  |
        | image             | correct       | 1/1 point           | 1 point possible   |
        | image             | incorrect     | 1 point possible    | 1 point possible   |

    Scenario: I can see my score on a problem when I answer it and after I reset it
        Given I am viewing a "<ProblemType>" problem with randomization "<Randomization>" with reset button on
        When I answer a "<ProblemType>" problem "<Correctness>ly"
        Then I should see a score of "<Score>"
        When I reset the problem
        Then I should see a score of "<Points Possible>"

        Examples:
        | ProblemType       | Correctness   | Score               | Points Possible    | Randomization |
        | drop down         | correct       | 1/1 point           | 1 point possible   | never         |
        | drop down         | incorrect     | 1 point possible    | 1 point possible   | never         |
        | multiple choice   | correct       | 1/1 point           | 1 point possible   | never         |
        | multiple choice   | incorrect     | 1 point possible    | 1 point possible   | never         |
        | checkbox          | correct       | 1/1 point           | 1 point possible   | never         |
        | checkbox          | incorrect     | 1 point possible    | 1 point possible   | never         |
        | radio             | correct       | 1/1 point           | 1 point possible   | never         |
        | radio             | incorrect     | 1 point possible    | 1 point possible   | never         |
        #| string            | correct       | 1/1 point           | 1 point possible   | never         |
        #| string            | incorrect     | 1 point possible    | 1 point possible   | never         |
        | numerical         | correct       | 1/1 point           | 1 point possible   | never         |
        | numerical         | incorrect     | 1 point possible    | 1 point possible   | never         |
        | formula           | correct       | 1/1 point           | 1 point possible   | never         |
        | formula           | incorrect     | 1 point possible    | 1 point possible   | never         |
        | script            | correct       | 2/2 points          | 2 points possible  | never         |
        | script            | incorrect     | 2 points possible   | 2 points possible  | never         |
        | image             | correct       | 1/1 point           | 1 point possible   | never         |
        | image             | incorrect     | 1 point possible    | 1 point possible   | never         |

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
        #| string            | 1 point possible   |
        | numerical         | 1 point possible   |
        | formula           | 1 point possible   |
        | script            | 2 points possible  |
        | image             | 1 point possible   |


    Scenario: I can reset the correctness of a problem after changing my answer
        Given I am viewing a "<ProblemType>" problem
        Then my "<ProblemType>" answer is marked "unanswered"
        When I answer a "<ProblemType>" problem "<InitialCorrectness>ly"
        And I input an answer on a "<ProblemType>" problem "<OtherCorrectness>ly"
        Then my "<ProblemType>" answer is marked "unanswered"
        And I reset the problem

        Examples:
        | ProblemType     | InitialCorrectness | OtherCorrectness |
        | drop down       | correct            | incorrect        |
        | drop down       | incorrect          | correct          |
        | checkbox        | correct            | incorrect        |
        | checkbox        | incorrect          | correct          |
        #| string          | correct            | incorrect        |
        #| string          | incorrect          | correct          |
        | numerical       | correct            | incorrect        |
        | numerical       | incorrect          | correct          |
        | formula         | correct            | incorrect        |
        | formula         | incorrect          | correct          |
        | script          | correct            | incorrect        |
        | script          | incorrect          | correct          |

    # Radio groups behave slightly differently than other types of checkboxes, because they
    # don't put their status to the top left of the boxes (like checkboxes do), thus, they'll
    # not ever have a status of "unanswered" once you've made an answer. They should simply NOT
    # be marked either correct or incorrect. Arguably this behavior should be changed; when it
    # is, these cases should move into the above Scenario.
    Scenario: I can reset the correctness of a radiogroup problem after changing my answer
        Given I am viewing a "<ProblemType>" problem
        When I answer a "<ProblemType>" problem "<InitialCorrectness>ly"
        Then my "<ProblemType>" answer is marked "<InitialCorrectness>"
        And I input an answer on a "<ProblemType>" problem "<OtherCorrectness>ly"
        Then my "<ProblemType>" answer is NOT marked "<InitialCorrectness>"
        And my "<ProblemType>" answer is NOT marked "<OtherCorrectness>"
        And I reset the problem

        Examples:
        | ProblemType     | InitialCorrectness | OtherCorrectness |
        | multiple choice | correct            | incorrect        |
        | multiple choice | incorrect          | correct          |
        | radio           | correct            | incorrect        |
        | radio           | incorrect          | correct          |


    Scenario: I can reset the correctness of a problem after submitting a blank answer
        Given I am viewing a "<ProblemType>" problem
        When I check a problem
        And I input an answer on a "<ProblemType>" problem "correctly"
        Then my "<ProblemType>" answer is marked "unanswered"

        Examples:
        | ProblemType       |
        | drop down         |
        | multiple choice   |
        | checkbox          |
        | radio             |
        #| string            |
        | numerical         |
        | formula           |
        | script            |
