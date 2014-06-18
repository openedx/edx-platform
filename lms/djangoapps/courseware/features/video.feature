@shard_2 @requires_stub_youtube
Feature: LMS.Video component
  As a student, I want to view course videos in LMS

  # 1
  Scenario: Verify that each video in each sub-section includes a transcript for non-Youtube countries
    Given youtube server is up and response time is 2 seconds
    And I am registered for the course "test_course"
    And I have a "subs_OEoXaMPEzfM.srt.sjson" transcript file in assets
    And I have a "subs_b7xgknqkQk8.srt.sjson" transcript file in assets
    And I have a "chinese_transcripts.srt" transcript file in assets
    And it has videos "A, B" in "Youtube_HTML5" mode in position "1" of sequential:
      | sub         |
      | OEoXaMPEzfM |
      | b7xgknqkQk8 |
    And a video "C" in "Youtube_HTML5" mode in position "2" of sequential:
      | transcripts                       |
      | {"zh": "chinese_transcripts.srt"} |
    And a video "D" in "Youtube_HTML5" mode in position "3" of sequential
    And I open the section with videos
    Then videos have rendered in "HTML5" mode
    And I see text in the captions:
      | text                |
      | Hi, welcome to Edx. |
      | Equal transcripts   |
    When I open video "C"
    Then the video has rendered in "HTML5" mode
    And I make sure captions are opened
    And I see "好 各位同学" text in the captions
    When I open video "D"
    Then the video has rendered in "HTML5" mode
    And the video does not show the captions

  # 4
  @skip_firefox
  Scenario: Quality button appears on play
    Given the course has a Video component in "Youtube" mode
    Then I see video button "quality" is hidden
    And I click video button "play"
    Then I see video button "quality" is visible

  # 5
  @skip_firefox
  Scenario: Quality button works correctly
    Given the course has a Video component in "Youtube" mode
    And I click video button "play"
    And I see video button "quality" is inactive
    And I click video button "quality"
    Then I see video button "quality" is active
