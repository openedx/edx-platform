@shard_2
Feature: LMS Video component
  As a student, I want to view course videos in LMS

  # 1
  Scenario: Video component stores position correctly when page is reloaded
    Given the course has a Video component in Youtube mode
    Then when I view the video it has rendered in Youtube mode
    And I click video button "play"
    Then I seek video to "10" seconds
    And I click video button "pause"
    And I reload the page
    And I click video button "play"
    Then I see video starts playing from "0:10" position

  # 2
  Scenario: Video component is fully rendered in the LMS in HTML5 mode
    Given the course has a Video component in HTML5 mode
    Then when I view the video it has rendered in HTML5 mode
    And all sources are correct

  # 3
  # Firefox doesn't have HTML5 (only mp4 - fix here)
  @skip_firefox
  Scenario: Autoplay is disabled in LMS for a Video component
    Given the course has a Video component in HTML5 mode
    Then when I view the video it does not have autoplay enabled

  # 4
  # Youtube testing
  Scenario: Video component is fully rendered in the LMS in Youtube mode with HTML5 sources
    Given youtube server is up and response time is 0.4 seconds
    And the course has a Video component in Youtube_HTML5 mode
    Then when I view the video it has rendered in Youtube mode

  # 5
  Scenario: Video component is not rendered in the LMS in Youtube mode with HTML5 sources
    Given youtube server is up and response time is 2 seconds
    And the course has a Video component in Youtube_HTML5 mode
    Then when I view the video it has rendered in HTML5 mode

  # 6
  Scenario: Video component is rendered in the LMS in Youtube mode without HTML5 sources
    Given youtube server is up and response time is 2 seconds
    And the course has a Video component in Youtube mode
    Then when I view the video it has rendered in Youtube mode

  # 7
  Scenario: Video component is rendered in the LMS in Youtube mode with HTML5 sources that doesn't supported by browser
    Given youtube server is up and response time is 2 seconds
    And the course has a Video component in Youtube_HTML5_Unsupported_Video mode
    Then when I view the video it has rendered in Youtube mode

  # 8
  Scenario: Video component is rendered in the LMS in HTML5 mode with HTML5 sources that doesn't supported by browser
    Given the course has a Video component in HTML5_Unsupported_Video mode
    Then error message is shown
    And error message has correct text

  # 9
  Scenario: Video component stores speed correctly when each video is in separate sequence
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

  # 10
  Scenario: Language menu works correctly in Video component
    Given the course has a Video component in Youtube mode:
      | transcripts           | sub         |
      | {"zh": "chinese_transcripts.srt"} | OEoXaMPEzfM |
    And I make sure captions are closed
    And I see video menu "language" with correct items
    And I select language with code "zh"
    Then I see "好 各位同学" text in the captions
    And I select language with code "en"
    And I see "Hi, welcome to Edx." text in the captions

  # 11
  Scenario: CC button works correctly w/o english transcript in HTML5 mode of Video component
    Given the course has a Video component in HTML5 mode:
      | transcripts           |
      | {"zh": "chinese_transcripts.srt"} |
    And I make sure captions are opened
    Then I see "好 各位同学" text in the captions

  # 12
  Scenario: CC button works correctly only w/ english transcript in HTML5 mode of Video component
    Given I am registered for the course "test_course"
    And I have a "subs_OEoXaMPEzfM.srt.sjson" transcript file in assets
    And it has a video in "HTML5" mode:
      | sub         |
      | OEoXaMPEzfM |
    And I make sure captions are opened
    Then I see "Hi, welcome to Edx." text in the captions

  # 13
  Scenario: CC button works correctly w/o english transcript in Youtube mode of Video component
    Given the course has a Video component in Youtube mode:
      | transcripts           |
      | {"zh": "chinese_transcripts.srt"} |
    And I make sure captions are opened
    Then I see "好 各位同学" text in the captions

  # 14
  Scenario: CC button works correctly if transcripts and sub fields are empty, but transcript file exists is assets (Youtube mode of Video component)
    Given I am registered for the course "test_course"
    And I have a "subs_OEoXaMPEzfM.srt.sjson" transcript file in assets
    And it has a video in "Youtube" mode
    And I make sure captions are opened
    Then I see "Hi, welcome to Edx." text in the captions

  # 15
  Scenario: CC button is hidden if no translations
    Given the course has a Video component in Youtube mode
    Then button "CC" is hidden

  # 16
  Scenario: Video is aligned correctly if transcript is visible in fullscreen mode
    Given the course has a Video component in HTML5 mode:
      | sub         |
      | OEoXaMPEzfM |
    And I make sure captions are opened
    And I click video button "fullscreen"
    Then I see video aligned correctly with enabled transcript

  # 17
  Scenario: Video is aligned correctly if transcript is hidden in fullscreen mode
    Given the course has a Video component in Youtube mode
    And I click video button "fullscreen"
    Then I see video aligned correctly without enabled transcript

  # 18
  Scenario: Video is aligned correctly on transcript toggle in fullscreen mode
    Given the course has a Video component in Youtube mode:
      | sub         |
      | OEoXaMPEzfM |
    And I make sure captions are opened
    And I click video button "fullscreen"
    Then I see video aligned correctly with enabled transcript
    And I click video button "CC"
    Then I see video aligned correctly without enabled transcript
