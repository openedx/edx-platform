@requires_stub_youtube
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
