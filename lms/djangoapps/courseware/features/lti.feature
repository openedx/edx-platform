@shard_1
Feature: LMS.LTI component
  As a student, I want to view LTI component in LMS.

  Scenario: LTI component in LMS is not rendered
  Given the course has correct LTI credentials
  And the course has an LTI component with incorrect fields
  Then I view the LTI and it is not rendered

  Scenario: LTI component in LMS is rendered
  Given the course has correct LTI credentials
  And the course has an LTI component filled with correct fields
  Then I view the LTI and it is rendered

  Scenario: LTI component in LMS is rendered incorrectly
  Given the course has incorrect LTI credentials
  And the course has an LTI component filled with correct fields
  Then I view the LTI but incorrect_signature warning is rendered
