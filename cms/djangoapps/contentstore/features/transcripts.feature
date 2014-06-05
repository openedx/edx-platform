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

    #1
    Scenario: Check input error messages
        Given I have created a Video component
        And I edit the component

        #User inputs html5 links with equal extension
        And I enter a "123.webm" source to field number 1
        And I enter a "456.webm" source to field number 2
        Then I see error message "file_type"
        # Currently we are working with 2nd field. It means, that if 2nd field
        # contain incorrect value, 1st and 3rd fields should be disabled until
        # 2nd field will be filled by correct correct value
        And I expect 1, 3 inputs are disabled
        When I clear fields
        And I expect inputs are enabled

        #User input URL with incorrect format
        And I enter a "http://link.c" source to field number 1
        Then I see error message "url_format"
        # Currently we are working with 1st field. It means, that if 1st field
        # contain incorrect value, 2nd and 3rd fields should be disabled until
        # 1st field will be filled by correct correct value
        And I expect 2, 3 inputs are disabled

        #User input URL with incorrect format
        And I enter a "http://goo.gl/pxxZrg" source to field number 1
        And I enter a "http://goo.gl/pxxZrg" source to field number 2
        Then I see error message "links_duplication"
        And I expect 1, 3 inputs are disabled

        And I clear fields
        And I expect inputs are enabled

        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I do not see error message
        And I expect inputs are enabled

    #2
    Scenario: Testing interaction with test youtube server
        Given I have created a Video component with subtitles
        And I edit the component
        # first part of url will be substituted by mock_youtube_server address
        # for t__eq_exist id server will respond with transcripts
        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "not found on edx"
        # t__eq_exist subs locally not presented at this moment
        And I see button "import"

        # for t_not_exist id server will respond with 404
        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I see status message "not found"
        And I do not see button "import"
        And I see button "disabled_download_to_edit"

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

    #4
    Scenario: Youtube id only: check "Found" state
        Given I have created a Video component with subtitles "t_not_exist"
        And I edit the component

        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I see status message "found"
        And I see value "t_not_exist" in the field "Default Timed Transcript"

    #5
    Scenario: Youtube id only: check "Found" state when user sets youtube_id with local and server subs and they are equal

        Given I have created a Video component with subtitles "t__eq_exist"
        And I edit the component

        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        And I see status message "found"
        And I see value "t__eq_exist" in the field "Default Timed Transcript"

    #6
    Scenario: Youtube id only: check "Found" state when user sets youtube_id with local and server subs and they are not  equal
        Given I have created a Video component with subtitles "t_neq_exist"
        And I edit the component

        And I enter a "http://youtu.be/t_neq_exist" source to field number 1
        And I see status message "replace"
        And I see button "replace"
        And I click transcript button "replace"
        And I see status message "found"
        And I see value "t_neq_exist" in the field "Default Timed Transcript"

    #7
    Scenario: html5 source only: check "Not Found" state
        Given I have created a Video component
        And I edit the component

        And I enter a "t_not_exist.mp4" source to field number 1
        Then I see status message "not found"
        And I see value "" in the field "Default Timed Transcript"

    #8
    Scenario: html5 source only: check "Found" state
        Given I have created a Video component with subtitles "t_not_exist"
        And I edit the component

        And I enter a "t_not_exist.mp4" source to field number 1
        Then I see status message "found"
        And I see value "t_not_exist" in the field "Default Timed Transcript"

    #9
    Scenario: User sets youtube_id w/o server but with local subs and one html5 link w/o subs
        Given I have created a Video component with subtitles "t_not_exist"
        And I edit the component

        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I see status message "found"

        And I enter a "test_video_name.mp4" source to field number 2
        Then I see status message "found"
        And I see value "t_not_exist" in the field "Default Timed Transcript"

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

    #11
    Scenario: User sets youtube_id w/o local but with server subs and one html5 link w/o transcripts w/o import action, then another one html5 link w/o transcripts
        Given I have created a Video component
        And I edit the component

        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "not found on edx"
        And I see button "import"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_not_exist.mp4" source to field number 2
        Then I see status message "not found on edx"
        And I see button "import"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_not_exist.webm" source to field number 3
        Then I see status message "not found on edx"
        And I see button "import"
        And I see button "upload_new_timed_transcripts"

    #12
    Scenario: Entering youtube (no importing), and 2 html5 sources without transcripts - "Not Found"
        Given I have created a Video component
        And I edit the component
        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I see status message "not found"
        And I see button "disabled_download_to_edit"
        And I see button "upload_new_timed_transcripts"
        And I enter a "t_not_exist.mp4" source to field number 2
        Then I see status message "not found"
        And I see button "upload_new_timed_transcripts"
        And I see button "disabled_download_to_edit"
        And I enter a "t_not_exist.webm" source to field number 3
        Then I see status message "not found"
        And I see button "disabled_download_to_edit"
        And I see button "upload_new_timed_transcripts"

    #13
    Scenario: Entering youtube with imported transcripts, and 2 html5 sources without transcripts - "Found"
        Given I have created a Video component
        And I edit the component

        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "not found on edx"
        And I see button "import"
        And I click transcript button "import"
        Then I see status message "found"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_not_exist.mp4" source to field number 2
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_not_exist.webm" source to field number 3
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"

    #14
    Scenario: Entering youtube w/o transcripts - html5 w/o transcripts - html5 with transcripts
        Given I have created a Video component with subtitles "t_neq_exist"
        And I edit the component

        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I see status message "not found"
        And I see button "disabled_download_to_edit"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_not_exist.mp4" source to field number 2
        Then I see status message "not found"
        And I see button "disabled_download_to_edit"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_neq_exist.webm" source to field number 3
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"

    #15
    Scenario: Entering youtube w/o imported transcripts - html5 w/o transcripts w/o import - html5 with transcripts
        Given I have created a Video component with subtitles "t_neq_exist"
        And I edit the component

        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "not found on edx"
        And I see button "import"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_not_exist.mp4" source to field number 2
        Then I see status message "not found on edx"
        And I see button "import"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_neq_exist.webm" source to field number 3
        Then I see status message "not found on edx"
        And I see button "import"
        And I see button "upload_new_timed_transcripts"

    #16
    Scenario: Entering youtube w/o imported transcripts - html5 with transcripts - html5 w/o transcripts w/o import
        Given I have created a Video component with subtitles "t_neq_exist"
        And I edit the component

        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "not found on edx"
        And I see button "import"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_neq_exist.mp4" source to field number 2
        Then I see status message "not found on edx"
        And I see button "import"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_not_exist.webm" source to field number 3
        Then I see status message "not found on edx"
        And I see button "import"
        And I see button "upload_new_timed_transcripts"

    #17
    Scenario: Entering youtube with imported transcripts - html5 with transcripts - html5 w/o transcripts
        Given I have created a Video component with subtitles "t_neq_exist"
        And I edit the component

        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "not found on edx"
        And I see button "import"
        And I click transcript button "import"
        Then I see status message "found"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_neq_exist.mp4" source to field number 2
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_not_exist.webm" source to field number 3
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"

    #18
    Scenario: Entering youtube with imported transcripts - html5 w/o transcripts - html5 with transcripts
        Given I have created a Video component with subtitles "t_neq_exist"
        And I edit the component

        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "not found on edx"
        And I see button "import"
        And I click transcript button "import"
        Then I see status message "found"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_not_exist.mp4" source to field number 2
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"

        And I enter a "t_neq_exist.webm" source to field number 3
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"

    #19
    Scenario: Entering html5 with transcripts - upload - youtube w/o transcripts
        Given I have created a Video component with subtitles "t__eq_exist"
        And I edit the component

        And I enter a "t__eq_exist.mp4" source to field number 1
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "uploaded_successfully"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"
        And I see value "t__eq_exist" in the field "Default Timed Transcript"

        And I enter a "http://youtu.be/t_not_exist" source to field number 2
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"

        And I enter a "uk_transcripts.webm" source to field number 3
        Then I see status message "found"

    #20
    Scenario: Enter 2 HTML5 sources with transcripts, they are not the same, choose
        Given I have created a Video component with subtitles "t_not_exist"
        And I edit the component

        And I enter a "uk_transcripts.mp4" source to field number 1
        Then I see status message "not found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "uploaded_successfully"
        And I see value "uk_transcripts" in the field "Default Timed Transcript"

        And I enter a "t_not_exist.webm" source to field number 2
        Then I see status message "replace"

        And I see choose button "uk_transcripts.mp4" number 1
        And I see choose button "t_not_exist.webm" number 2
        And I click transcript button "choose" number 2
        And I see value "uk_transcripts|t_not_exist" in the field "Default Timed Transcript"

    # Flaky test fails occasionally in master. https://edx-wiki.atlassian.net/browse/BLD-927
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

    #22
    Scenario: Work with 1 field only: Enter HTML5 source with transcripts - save -> change it to another one HTML5 source w/o transcripts - click on use existing ->  change it to another one HTML5 source w/o transcripts - do not click on use existing -> change it to another one HTML5 source w/o transcripts - click on use existing
        Given I have created a Video component with subtitles "t_not_exist"
        And I edit the component

        And I enter a "t_not_exist.mp4" source to field number 1
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"
        And I see value "t_not_exist" in the field "Default Timed Transcript"

        And I save changes
        And I edit the component

        And I enter a "video_name_2.mp4" source to field number 1
        Then I see status message "use existing"
        And I see button "use_existing"
        And I click transcript button "use_existing"
        And I see value "video_name_2" in the field "Default Timed Transcript"

        And I enter a "video_name_3.mp4" source to field number 1
        Then I see status message "use existing"
        And I see button "use_existing"

        And I enter a "video_name_4.mp4" source to field number 1
        Then I see status message "use existing"
        And I see button "use_existing"
        And I click transcript button "use_existing"
        And I see value "video_name_4" in the field "Default Timed Transcript"

    #23
    Scenario: Work with 2 fields: Enter HTML5 source with transcripts - save -> change it to another one HTML5 source w/o transcripts - do not click on use existing ->  add another one HTML5 source w/o transcripts - click on use existing
        Given I have created a Video component with subtitles "t_not_exist"
        And I edit the component

        And I enter a "t_not_exist.mp4" source to field number 1
        Then I see status message "found"
        And I see button "download_to_edit"
        And I see button "upload_new_timed_transcripts"

        And I save changes
        And I edit the component

        And I enter a "video_name_2.mp4" source to field number 1
        Then I see status message "use existing"
        And I see button "use_existing"

        And I enter a "video_name_3.webm" source to field number 2
        Then I see status message "use existing"
        And I see button "use_existing"
        And I click transcript button "use_existing"
        And I see value "video_name_2|video_name_3" in the field "Default Timed Transcript"

    #24 Uploading subtitles with different file name than file
    Scenario: File name and name of subs are different
        Given I have created a Video component
        And I edit the component

        And I enter a "video_name_1.mp4" source to field number 1
        And I see status message "not found"
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "uploaded_successfully"
        And I see value "video_name_1" in the field "Default Timed Transcript"

        And I save changes
        Then when I view the video it does show the captions

        And I edit the component
        Then I see status message "found"

    #25
    # Video can have filled item.sub, but doesn't have subs file.
    # In this case, after changing this video by another one without subs
    # `Not found` message should appear ( not `use existing`).
    Scenario: Video w/o subs - another video w/o subs - Not found message
        Given I have created a Video component
        And I edit the component

        And I enter a "video_name_1.mp4" source to field number 1
        Then I see status message "not found"

    #26
    Scenario: Subtitles are copied for every html5 video source
        Given I have created a Video component
        And I edit the component

        And I enter a "video_name_1.mp4" source to field number 1
        And I see status message "not found"

        And I enter a "video_name_2.webm" source to field number 2
        And I see status message "not found"
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "uploaded_successfully"
        And I see value "video_name_1|video_name_2" in the field "Default Timed Transcript"

        And I clear field number 1
        Then I see status message "found"
        And I see value "video_name_2" in the field "Default Timed Transcript"

    #27
    Scenario: Upload button for single youtube id
        Given I have created a Video component
        And I edit the component

        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I see status message "not found"
        And I see button "upload_new_timed_transcripts"
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "uploaded_successfully"

        And I save changes
        Then when I view the video it does show the captions

        And I edit the component
        Then I see status message "found"

    #28
    Scenario: Upload button for youtube id with html5 ids
        Given I have created a Video component
        And I edit the component

        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I see status message "not found"
        And I see button "upload_new_timed_transcripts"

        And I enter a "video_name_1.mp4" source to field number 2
        Then I see status message "not found"
        And I see button "upload_new_timed_transcripts"

        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "uploaded_successfully"
        And I clear field number 1
        Then I see status message "found"
        And I see value "video_name_1" in the field "Default Timed Transcript"

        And I save changes
        Then when I view the video it does show the captions
        And I edit the component
        Then I see status message "found"

    #29
    Scenario: Change transcripts field in Advanced tab
        Given I have created a Video component with subtitles "t_not_exist"
        And I edit the component

        And I enter a "video_name_1.mp4" source to field number 1
        Then I see status message "not found"

        And I open tab "Advanced"
        And I set value "t_not_exist" to the field "Default Timed Transcript"

        And I save changes
        Then when I view the video it does show the captions
        And I edit the component

        Then I see status message "found"
        And I see value "video_name_1" in the field "Default Timed Transcript"

    #30
    Scenario: Check non-ascii (chinise) transcripts
        Given I have created a Video component
        And I edit the component

        And I enter a "video_name_1.mp4" source to field number 1
        Then I see status message "not found"
        And I upload the transcripts file "chinese_transcripts.srt"

        Then I see status message "uploaded_successfully"

        And I save changes
        Then when I view the video it does show the captions

    #31
    Scenario: Check saving module metadata on switching between tabs
        Given I have created a Video component with subtitles "t_not_exist"
        And I edit the component

        And I enter a "video_name_1.mp4" source to field number 1
        Then I see status message "not found"

        And I open tab "Advanced"
        And I set value "t_not_exist" to the field "Default Timed Transcript"
        And I open tab "Basic"
        Then I see status message "found"

        And I save changes
        Then when I view the video it does show the captions
        And I edit the component

        Then I see status message "found"
        And I see value "video_name_1" in the field "Default Timed Transcript"

    #32
    Scenario: After clearing Transcripts field in the Advanced tab "not found" message should be visible w/o saving
        Given I have created a Video component
        And I edit the component

        And I enter a "t_not_exist.mp4" source to field number 1
        Then I see status message "not found"
        And I upload the transcripts file "chinese_transcripts.srt"
        Then I see status message "uploaded_successfully"

        And I open tab "Advanced"
        And I set value "" to the field "Default Timed Transcript"
        And I open tab "Basic"
        Then I see status message "not found"

        And I save changes
        Then when I view the video it does not show the captions
        And I edit the component

        Then I see status message "not found"
        And I see value "" in the field "Default Timed Transcript"

    #33
    Scenario: After clearing Transcripts field in the Advanced tab "not found" message should be visible with saving
        Given I have created a Video component
        And I edit the component

        And I enter a "t_not_exist.mp4" source to field number 1
        Then I see status message "not found"
        And I upload the transcripts file "chinese_transcripts.srt"
        Then I see status message "uploaded_successfully"

        And I save changes
        Then I see "好 各位同学" text in the captions
        And I edit the component

        And I open tab "Advanced"
        And I set value "" to the field "Default Timed Transcript"
        And I open tab "Basic"
        Then I see status message "not found"

        And I save changes
        Then when I view the video it does not show the captions
        And I edit the component

        Then I see status message "not found"
        And I see value "" in the field "Default Timed Transcript"

    #34
    Scenario: Video with existing subs - Advanced tab - change to another one subs - Basic tab - Found message - Save - see correct subs
        Given I have created a Video component with subtitles "t_not_exist"
        And I edit the component

        And I enter a "video_name_1.mp4" source to field number 1
        Then I see status message "not found"

        And I upload the transcripts file "chinese_transcripts.srt"
        Then I see status message "uploaded_successfully"

        And I save changes
        Then when I view the video it does show the captions
        And I see "好 各位同学" text in the captions
        And I edit the component

        And I open tab "Advanced"
        And I set value "t_not_exist" to the field "Default Timed Transcript"
        And I open tab "Basic"
        Then I see status message "found"

        And I save changes
        Then when I view the video it does show the captions
        And I see "LILA FISHER: Hi, welcome to Edx." text in the captions

    #35
    Scenario: After reverting Transcripts field in the Advanced tab "not found" message should be visible
        Given I have created a Video component
        And I edit the component

        And I enter a "t_not_exist.mp4" source to field number 1
        Then I see status message "not found"
        And I upload the transcripts file "chinese_transcripts.srt"
        Then I see status message "uploaded_successfully"

        And I save changes
        Then I see "好 各位同学" text in the captions
        And I edit the component

        And I open tab "Advanced"
        And I revert the transcript field "Default Timed Transcript"

        And I save changes
        Then when I view the video it does not show the captions
        And I edit the component
        Then I see status message "not found"

    #36 Uploading subtitles for file with periods in it should properly set the transcript name and keep the periods
    Scenario: File name and name of subs are different
        Given I have created a Video component
        And I edit the component

        And I enter a "video_name_1.1.2.mp4" source to field number 1
        And I see status message "not found"
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "uploaded_successfully"
        And I see value "video_name_1.1.2" in the field "Default Timed Transcript"

        And I save changes
        Then when I view the video it does show the captions

        And I edit the component
        Then I see status message "found"

    #37 Uploading subtitles with different file name than file
    Scenario: Shortened link: File name and name of subs are different
        Given I have created a Video component
        And I edit the component

        And I enter a "http://goo.gl/pxxZrg" source to field number 1
        And I see status message "not found"
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "uploaded_successfully"
        And I see value "pxxZrg" in the field "Default Timed Transcript"

        And I save changes
        Then when I view the video it does show the captions

        And I edit the component
        Then I see status message "found"

    #38 Uploading subtitles with different file name than file
    Scenario: Relative link: File name and name of subs are different
        Given I have created a Video component
        And I edit the component

        And I enter a "/gizmo.webm" source to field number 1
        And I see status message "not found"
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "uploaded_successfully"
        And I see value "gizmo" in the field "Default Timed Transcript"

        And I save changes
        Then when I view the video it does show the captions

        And I edit the component
        Then I see status message "found"
