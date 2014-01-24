@shard_1
Feature: LMS.LTI component
  As a student, I want to view LTI component in LMS.

  #1
  Scenario: LTI component in LMS with no launch_url is not rendered
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with no_launch_url fields:
  | open_in_a_new_page |
  | False              |
  Then I view the LTI and error is shown

  #2
  Scenario: LTI component in LMS with incorrect lti_id is rendered incorrectly
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with incorrect_lti_id fields:
  | open_in_a_new_page |
  | False              |
  Then I view the LTI but incorrect_signature warning is rendered

  #3
  Scenario: LTI component in LMS is rendered incorrectly
  Given the course has incorrect LTI credentials
  And the course has an LTI component with correct fields:
  | open_in_a_new_page |
  | False              |
  Then I view the LTI but incorrect_signature warning is rendered

  #4
  Scenario: LTI component in LMS is correctly rendered in new page
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields
  Then I view the LTI and it is rendered in new page

  #5
  Scenario: LTI component in LMS is correctly rendered in iframe
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | open_in_a_new_page |
  | False              |
  Then I view the LTI and it is rendered in iframe

  #6
  Scenario: Graded LTI component in LMS is correctly works
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | open_in_a_new_page | weight | is_graded | has_score |
  | False              | 10     | True      | True      |
  And I submit answer to LTI question
  And I click on the "Progress" tab
  Then I see text "Problem Scores: 5/10"
  And I see graph with total progress "5%"
  Then I click on the "Instructor" tab
  And I click on the "Gradebook" tab
  And I see in the gradebook table that "HW" is "50"
  And I see in the gradebook table that "Total" is "5"

  #7
  Scenario: Graded LTI component in LMS is correctly works with beta testers
  Given the course has correct LTI credentials with registered BetaTester
  And the course has an LTI component with correct fields:
  | open_in_a_new_page | weight | is_graded | has_score |
  | False              | 10     | True      | True      |
  And I submit answer to LTI question
  And I click on the "Progress" tab
  Then I see text "Problem Scores: 5/10"
  And I see graph with total progress "5%"


