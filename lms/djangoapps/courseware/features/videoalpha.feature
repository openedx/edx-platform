Feature: Video Alpha component
  As a student, I want to view course videos in LMS.

  Scenario: Alpha Autoplay is enabled in LMS
    Given the course has a VideoAlpha component
    Then when I view the video alpha it has autoplay enabled
