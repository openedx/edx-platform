Feature: Open ended grading
  As a student in an edX course
  In order to complete the courseware questions
  I want the machine learning grading to be functional

    Scenario: I can submit an answer for instructor grading
    Given I am registered for course "MITx/3.091x/2012_Fall"
    And I log in
    And I navigate to an openended question
    When I enter the answer "I have no idea."
    And I press the "Check" button
    Then I see the grader status "Submitted for grading"
    And I see the grader message "Feedback not yet available."

    Scenario: I can submit an answer for instructor grading
    Given I am staff for course "MITx/3.091x/2012_Fall"
    And I log in
    And I navigate to an openended question
    When I submit the answer "I love Chemistry."
    And I visit the staff grading page
    Then my answer is queued for instructor grading