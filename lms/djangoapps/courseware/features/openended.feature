Feature: LMS.Open ended grading
  As a student in an edX course
  In order to complete the courseware questions
  I want the machine learning grading to be functional

    # Commenting these all out right now until we can
    # make a reference implementation for a course with
    # an open ended grading problem that is always available
    #
    # Scenario: An answer that is too short is rejected
    # Given I navigate to an openended question
    # And I enter the answer "z"
    # When I press the "Check" button
    # And I wait for "8" seconds
    # And I see the grader status "Submitted for grading"
    # And I press the "Recheck for Feedback" button
    # Then I see the red X
    # And I see the grader score "0"

    # Scenario: An answer with too many spelling errors is rejected
    # Given I navigate to an openended question
    # And I enter the answer "az"
    # When I press the "Check" button
    # And I wait for "8" seconds
    # And I see the grader status "Submitted for grading"
    # And I press the "Recheck for Feedback" button
    # Then I see the red X
    # And I see the grader score "0"
    # When I click the link for full output
    # Then I see the spelling grading message "More spelling errors than average."

    # Scenario: An answer makes its way to the instructor dashboard
    # Given I navigate to an openended question as staff
    # When I submit the answer "I love Chemistry."
    # And I wait for "8" seconds
    # And I visit the staff grading page
    # Then my answer is queued for instructor grading
