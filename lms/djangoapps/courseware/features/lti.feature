@shard_1
Feature: LMS.LTI component
  As a student, I want to view LTI component in LMS.

  Scenario: LTI component in LMS with no launch_url is not rendered
  Given the course has correct LTI credentials
  And the course has an LTI component with no_launch_url fields, new_page is false
  Then I view the LTI and error is shown

  Scenario: LTI component in LMS with incorrect lti_id is rendered incorrectly
  Given the course has correct LTI credentials
  And the course has an LTI component with incorrect_lti_id fields, new_page is false
  Then I view the LTI but incorrect_signature warning is rendered

  Scenario: LTI component in LMS is rendered incorrectly
  Given the course has incorrect LTI credentials
  And the course has an LTI component with correct fields, new_page is false
  Then I view the LTI but incorrect_signature warning is rendered

  Scenario: LTI component in LMS is correctly rendered in new page
  Given the course has correct LTI credentials
  And the course has an LTI component with correct fields, new_page is true
  Then I view the LTI and it is rendered in new page

  Scenario: LTI component in LMS is correctly rendered in iframe
  Given the course has correct LTI credentials
  And the course has an LTI component with correct fields, new_page is false
  Then I view the LTI and it is rendered in iframe
