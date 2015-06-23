@shard_2 @requires_stub_youtube
Feature: LMS.Video component
  As a student, I want to view course videos in LMS

  # 1
  Scenario: Verify that each video in sub-section includes a transcript for Youtube and non-Youtube countries
    Given youtube server is up and response time is 2 seconds
    And I am registered for the course "test_course"
    And I have a "subs_3_yD_cEKoCk.srt.sjson" transcript file in assets
    And I have a "subs_b7xgknqkQk8.srt.sjson" transcript file in assets
    And I have a "chinese_transcripts.srt" transcript file in assets
    And it has videos "A, B" in "Youtube_HTML5" mode in position "1" of sequential:
      | sub         |
      | 3_yD_cEKoCk |
      | b7xgknqkQk8 |
    And a video "C" in "Youtube_HTML5" mode in position "2" of sequential:
      | transcripts                       |
      | {"zh": "chinese_transcripts.srt"} |
    And a video "D" in "Youtube_HTML5" mode in position "3" of sequential
    And I open the section with videos
    Then videos have rendered in "HTML5" mode
    And I see text in the captions:
      | text              |
      | Welcome to edX.   |
      | Equal transcripts |
    When I open video "C"
    Then the video has rendered in "YOUTUBE" mode
    And I make sure captions are opened
    And I see "好 各位同学" text in the captions
    When I open video "D"
    Then the video has rendered in "YOUTUBE" mode
    And I make sure captions are opened
