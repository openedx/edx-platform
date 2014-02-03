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
    Given youtube server is up and response time is 0.4 seconds
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

  # 8
  Scenario: Video component stores speed correctly when each video is in separate sequence.
    Given I am registered for the course "test_course"
    And it has a video "A" in "Youtube" mode in position "1" of sequential
    And a video "B" in "Youtube" mode in position "2" of sequential
    And a video "C" in "Youtube" mode in position "3" of sequential
    And I open the section with videos
    And I select the "2.0" speed on video "A"
    And I select the "0.50" speed on video "B"
    When I open video "C"
    Then video "C" should start playing at speed "0.50"
    When I open video "A"
    Then video "A" should start playing at speed "2.0"
    And I reload the page
    When I open video "A"
    Then video "A" should start playing at speed "2.0"
    And I select the "1.0" speed on video "A"
    When I open video "B"
    Then video "B" should start playing at speed "0.50"
    When I open video "C"
    Then video "C" should start playing at speed "1.0"

  # 9
  Scenario: Video components' language menu works correctly
    Given the course has a Video component in Youtube mode:
    | transcripts           | sub         |
    | {"zh": "OEoXaMPEzfM"} | OEoXaMPEzfM |
    And I make sure captions are closed
    And I see video menu "language" with following items:
    | lang-code     | label       |
    | en            | English     |
    | zh            | Chinese     |
    And I select language with code "zh"
    Then I see "好 各位同学" text in the captions
    And I select language with code "en"
    And I see "Hi, welcome to Edx." text in the captions
