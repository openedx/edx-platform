@shard_3 @requires_stub_youtube
Feature: CMS Transcripts
  As a course author, I want to be able to create video components

    # For transcripts acceptance tests there are 3 available caption
    # files. They can be used to test various transcripts features. Two of
    # them can be imported from YouTube.
    #
    # The length of each file name is 11 characters. This is because the
    # YouTube's ID length is 11 characters. If file name is not of length 11,
    # front-end validation will not pass.
    #
    #     t__eq_exist - this file exists on YouTube, and can be imported
    #                   via the transcripts menu; after import, this file will
    #                   be equal to the one stored locally
    #     t_neq_exist - same as above, except local file will differ from the
    #                   one stored on YouTube
    #     t_not_exist - this file does not exist on YouTube; it exists locally

    #3
    Scenario: Youtube id only: check "not found" and "import" states
        Given I have created a Video component with subtitles
        And I edit the component

        # Not found: w/o local or server subs
        And I remove "t_not_exist" transcripts id from store
        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I see status message "not found"
        And I see value "" in the field "Default Timed Transcript"

        # Import: w/o local but with server subs
        And I remove "t__eq_exist" transcripts id from store
        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "not found on edx"
        And I see button "import"
        And I click transcript button "import"
        Then I see status message "found"
        And I see button "upload_new_timed_transcripts"
        And I see button "download_to_edit"
        And I see value "t__eq_exist" in the field "Default Timed Transcript"


    # Disabled 1/29/14 due to flakiness observed in master
    #10
    #Scenario: User sets youtube_id w/o local but with server subs and one html5 link w/o subs
    #    Given I have created a Video component
    #    And I edit the component
    #
    #    And I enter a "http://youtu.be/t__eq_exist" source to field number 1
    #    Then I see status message "not found on edx"
    #    And I see button "import"
    #    And I click transcript button "import"
    #    Then I see status message "found"
    #
    #    And I enter a "t_not_exist.mp4" source to field number 2
    #    Then I see status message "found"
    #    And I see value "t__eq_exist" in the field "Default Timed Transcript"

    # Flaky test fails occasionally in master. https://openedx.atlassian.net/browse/BLD-892
    #21
    #Scenario: Work with 1 field only: Enter HTML5 source with transcripts - save - > change it to another one HTML5 source w/o #transcripts - click on use existing - >  change it to another one HTML5 source w/o transcripts - click on use existing
    #    Given I have created a Video component with subtitles "t_not_exist"
    #    And I edit the component
    #
    #    And I enter a "t_not_exist.mp4" source to field number 1
    #    Then I see status message "found"
    #    And I see button "download_to_edit"
    #    And I see button "upload_new_timed_transcripts"
    #    And I see value "t_not_exist" in the field "Default Timed Transcript"
    #
    #    And I save changes
    #    And I edit the component
    #
    #    And I enter a "video_name_2.mp4" source to field number 1
    #    Then I see status message "use existing"
    #    And I see button "use_existing"
    #    And I click transcript button "use_existing"
    #    And I see value "video_name_2" in the field "Default Timed Transcript"
    #
    #    And I enter a "video_name_3.mp4" source to field number 1
    #    Then I see status message "use existing"
    #    And I see button "use_existing"
    #    And I click transcript button "use_existing"
    #    And I see value "video_name_3" in the field "Default Timed Transcript"
