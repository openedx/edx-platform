@shard_1 @requires_stub_lti
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
  | open_in_a_new_page | weight | graded    | has_score |
  | False              | 10     | True      | True      |
  And I submit answer to LTI 1 question
  And I click on the "Progress" tab
  Then I see text "Problem Scores: 1. 5/10"
  And I see graph with total progress "5%"
  Then I click on the "Instructor" tab
  And I click the "Student Admin" button
  And I click on the "View Gradebook" link
  And I see in the gradebook table that "HW" is "50"
  And I see in the gradebook table that "Total" is "5"

  #7
  Scenario: Graded LTI component in LMS role's masquerading correctly works
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | open_in_a_new_page | has_score |
  | False              | True      |
  And I view the LTI and it is rendered in iframe
  And I see in iframe that LTI role is Instructor
  And I switch to student
  And I view the LTI and it is rendered in iframe
  Then I see in iframe that LTI role is Student

  #8
  Scenario: Graded LTI component in LMS is correctly works with beta testers
  Given the course has correct LTI credentials with registered BetaTester
  And the course has an LTI component with correct fields:
  | open_in_a_new_page | weight | graded    | has_score |
  | False              | 10     | True      | True      |
  And I submit answer to LTI 1 question
  And I click on the "Progress" tab
  Then I see text "Problem Scores: 1. 5/10"
  And I see graph with total progress "5%"

  #9
  Scenario: Graded LTI component in LMS is correctly works with LTI2v0 PUT callback
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | open_in_a_new_page | weight | graded    | has_score |
  | False              | 10     | True      | True      |
  And I submit answer to LTI 2 question
  And I click on the "Progress" tab
  Then I see text "Problem Scores: 8/10"
  And I see graph with total progress "8%"
  Then I click on the "Instructor" tab
  And I click the "Student Admin" button
  And I click on the "View Gradebook" link
  And I see in the gradebook table that "HW" is "80"
  And I see in the gradebook table that "Total" is "8"
  And I visit the LTI component
  Then I see LTI component progress with text "(8.0 / 10.0 points)"
  Then I see LTI component feedback with text "This is awesome."

  #10
  Scenario: Graded LTI component in LMS is correctly works with LTI2v0 PUT delete callback
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | open_in_a_new_page | weight | graded    | has_score |
  | False              | 10     | True      | True      |
  And I submit answer to LTI 2 question
  And I visit the LTI component
  Then I see LTI component progress with text "(8.0 / 10.0 points)"
  Then I see LTI component feedback with text "This is awesome."
  And the LTI provider deletes my grade and feedback
  And I visit the LTI component (have to reload)
  Then I see LTI component progress with text "(10.0 points possible)"
  Then in the LTI component I do not see feedback
  And I click on the "Progress" tab
  Then I see text "Problem Scores: 0/10"
  And I see graph with total progress "0%"
  Then I click on the "Instructor" tab
  And I click the "Student Admin" button
  And I click on the "View Gradebook" link
  And I see in the gradebook table that "HW" is "0"
  And I see in the gradebook table that "Total" is "0"

  #11
  Scenario: LTI component that set to hide_launch and open_in_a_new_page shows no button
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | open_in_a_new_page | hide_launch |
  | False              | True        |
  Then in the LTI component I do not see a launch button
  Then I see LTI component module title with text "LTI (External resource)"

  #12
  Scenario: LTI component that set to hide_launch and not open_in_a_new_page shows no iframe
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | open_in_a_new_page | hide_launch |
  | True               | True        |
  Then in the LTI component I do not see an provider iframe
  Then I see LTI component module title with text "LTI (External resource)"

  #13
  Scenario: LTI component button text is correctly displayed
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | button_text        |
  | Launch Application |
  Then I see LTI component button with text "Launch Application"

  #14
  Scenario: LTI component description is correctly displayed
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | description             |
  | Application description |
  Then I see LTI component description with text "Application description"

  #15
  Scenario: LTI component requests permission for username and is rejected
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | ask_to_send_username |
  | True                 |
  Then I view the permission alert
  Then I reject the permission alert and do not view the LTI

  #16
  Scenario: LTI component requests permission for username and displays LTI when accepted
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | ask_to_send_username |
  | True                 |
  Then I view the permission alert
  Then I accept the permission alert and view the LTI

  #17
  Scenario: LTI component requests permission for email and is rejected
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | ask_to_send_email |
  | True              |
  Then I view the permission alert
  Then I reject the permission alert and do not view the LTI

  #18
  Scenario: LTI component requests permission for email and displays LTI when accepted
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | ask_to_send_email |
  | True              |
  Then I view the permission alert
  Then I accept the permission alert and view the LTI

  #19
  Scenario: LTI component requests permission for email and username and is rejected
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | ask_to_send_email | ask_to_send_username |
  | True              | True                 |
  Then I view the permission alert
  Then I reject the permission alert and do not view the LTI

  #20
  Scenario: LTI component requests permission for email and username and displays LTI when accepted
  Given the course has correct LTI credentials with registered Instructor
  And the course has an LTI component with correct fields:
  | ask_to_send_email | ask_to_send_username |
  | True              | True                 |
  Then I view the permission alert
  Then I accept the permission alert and view the LTI
