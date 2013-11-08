@shard_2
Feature: LMS.Video component
  As a student, I want to view course videos in LMS.

  # 1
  Scenario: Video component is fully rendered in the LMS in HTML5 mode
    Given the course has a Video component in HTML5 mode
    Then when I view the video it has rendered in HTML5 mode
    And all sources are correct

  # 2
  # Firefox doesn't have HTML5 (only mp4 - fix here)
  @skip_firefox
  Scenario: Autoplay is disabled in LMS for a Video component
    Given the course has a Video component in HTML5 mode
    Then when I view the video it does not have autoplay enabled

  # 3
  # Youtube testing
  Scenario: Video component is fully rendered in the LMS in Youtube mode with HTML5 sources
    Given youtube server is up and response time is  0.4 seconds
    And the course has a Video component in Youtube_HTML5 mode
    Then when I view the video it has rendered in Youtube mode

  # 4
  Scenario: Video component is not rendered in the LMS in Youtube mode with HTML5 sources
    Given youtube server is up and response time is 2 seconds
    And the course has a Video component in Youtube_HTML5 mode
    Then when I view the video it has rendered in HTML5 mode

  # 5
  Scenario: Video component is rendered in the LMS in Youtube mode without HTML5 sources
    Given youtube server is up and response time is 2 seconds
    And the course has a Video component in Youtube mode
    Then when I view the video it has rendered in Youtube mode

  # 6
  Scenario: Video component is rendered in the LMS in Youtube mode with HTML5 sources that doesn't supported by browser
    Given youtube server is up and response time is 2 seconds
    And the course has a Video component in Youtube_HTML5_Unsupported_Video mode
    Then when I view the video it has rendered in Youtube mode

  # 7
  Scenario: Video component is rendered in the LMS in HTML5 mode with HTML5 sources that doesn't supported by browser
    Given the course has a Video component in HTML5_Unsupported_Video mode
    Then error message is shown
    And error message has correct text
