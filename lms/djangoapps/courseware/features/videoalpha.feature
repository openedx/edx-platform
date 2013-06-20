Feature: Video Alpha component
  As a student, I want to view course videos in LMS.

  Scenario: Autoplay is enabled in LMS
    Given the course has a Video Alpha component
    Then when I view the Video Alpha it has autoplay enabled
