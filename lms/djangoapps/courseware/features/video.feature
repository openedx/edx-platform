@shard_2
Feature: LMS.Video component
  As a student, I want to view course videos in LMS

  # 1
  Scenario: Multiple videos in sequentials all load and work, switching between sequentials
    Given I am registered for the course "test_course"
    And it has a video "A" in "Youtube" mode in position "1" of sequential
    And a video "B" in "HTML5" mode in position "1" of sequential
    And a video "C" in "Youtube" mode in position "1" of sequential
    And a video "D" in "Youtube" mode in position "1" of sequential
    And a video "E" in "Youtube" mode in position "2" of sequential
    And a video "F" in "Youtube" mode in position "2" of sequential
    And a video "G" in "Youtube" mode in position "2" of sequential
    And I open the section with videos
    Then video "A" should start playing at speed "1.0"
    And I select the "2.0" speed on video "B"
    And I select the "2.0" speed on video "C"
    And I select the "2.0" speed on video "D"
    When I open video "E"
    Then video "E" should start playing at speed "2.0"
    And I select the "1.0" speed on video "F"
    And I select the "1.0" speed on video "G"
    When I open video "A"
    Then video "A" should start playing at speed "2.0"

  # 2
  Scenario: Video component stores speed correctly when each video is in separate sequence
    Given I am registered for the course "test_course"
    And it has a video "A" in "Youtube" mode in position "1" of sequential
    And a video "B" in "Youtube" mode in position "2" of sequential
    And a video "C" in "HTML5" mode in position "3" of sequential
    And I open the section with videos
    And I select the "2.0" speed on video "A"
    And I select the "0.50" speed on video "B"
    When I open video "C"
    Then video "C" should start playing at speed "0.75"
    When I open video "A"
    Then video "A" should start playing at speed "2.0"
    And I reload the page with video
    When I open video "A"
    Then video "A" should start playing at speed "2.0"
    And I select the "1.0" speed on video "A"
    When I open video "B"
    Then video "B" should start playing at speed "0.50"
    When I open video "C"
    Then video "C" should start playing at speed "1.0"

  # 9
#  Scenario: Youtube video has correct transcript if fields for other speeds are filled
#    Given I am registered for the course "test_course"
#    And I have a "subs_OEoXaMPEzfM.srt.sjson" transcript file in assets
#    And I have a "subs_b7xgknqkQk8.srt.sjson" transcript file in assets
#    And it has a video in "Youtube" mode:
#      | sub         | youtube_id_1_5 |
#      | OEoXaMPEzfM | b7xgknqkQk8    |
#    And I make sure captions are opened
#    Then I see "Hi, welcome to Edx." text in the captions
#    And I select the "1.50" speed
#    And I reload the page with video
#    Then I see "Hi, welcome to Edx." text in the captions
    # The 1:56 time is the duration from metadata. 1:54 time is the duration reported
    # by the video API once the video starts playing. The next step is correct because
    # "1:56" is the duration in the VCR timer before the video plays.
#    And I see duration "1:56"

  # 3
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

  # 29 Disabled 4/8/14 after intermittent failures in master
  #Scenario: Transcripts are available on different speeds of Flash mode
  #  Given I am registered for the course "test_course"
  #  And I have a "subs_OEoXaMPEzfM.srt.sjson" transcript file in assets
  #  And it has a video in "Flash" mode
  #  Then the video has rendered in "Flash" mode
  #  And I make sure captions are opened
  #  And I see "Hi, welcome to Edx." text in the captions
  #  Then I select the "1.50" speed
  #  And I see "Hi, welcome to Edx." text in the captions
  #  Then I select the "0.75" speed
  #  And I see "Hi, welcome to Edx." text in the captions
  #  Then I select the "1.25" speed
  #  And I see "Hi, welcome to Edx." text in the captions

  # 30 Disabled 4/8/14 after intermittent failures in master
  #Scenario: Elapsed time calculates correctly on different speeds of Flash mode
  #  Given I am registered for the course "test_course"
  #  And I have a "subs_OEoXaMPEzfM.srt.sjson" transcript file in assets
  #  And it has a video in "Flash" mode
  #  And I make sure captions are opened
  #  Then I select the "1.50" speed
  #  And I click video button "pause"
  #  And I click on caption line "4", video module shows elapsed time "7"
  #  Then I select the "0.75" speed
  #  And I click video button "pause"
  #  And I click on caption line "3", video module shows elapsed time "9"
  #  Then I select the "1.25" speed
  #  And I click video button "pause"
  #  And I click on caption line "2", video module shows elapsed time "4"

  # 31 Disabled 4/8/14 after intermittent failures in master
  #Scenario: Video component stores position correctly when page is reloaded
  #  Given the course has a Video component in "Youtube" mode
  #  When the video has rendered in "Youtube" mode
  #  And I click video button "play"
  #  And I click video button "pause"
  #  Then I seek video to "0:10" position
  #  And I click video button "play"
  #  And I click video button "pause"
  #  And I reload the page with video
  #  Then I see video slider at "0:10" position
