Feature: LTI component
  As a student, I want to view LTI component in LMS.

  Scenario: LTI component in LMS is not rendered
  Given the course has a LTI component with empty fields
  Then I view the LTI and it is not rendered

  Scenario: LTI component in LMS is rendered
  Given the course has a LTI component filled with correct data
  Then I view the LTI and it is rendered
