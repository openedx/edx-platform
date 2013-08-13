Feature: Video Component Editor
  As a course author, I want to be able to create video components.

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
        And I enter a 123.webm source to field number 1
        And I enter a 456.webm source to field number 2
        Then I see file_type error message
        # Currently we are working with 2nd field. It means, that if 2nd field
        # contain incorrect value, 1st and 3rd fields should be disabled until
        # 2nd field will be filled by correct correct value
        And I expect 1, 3 inputs are disabled
        When I clear fields
        And I expect inputs are enabled

        #User input URL with incorrect format
        And I enter a htt://link.c source to field number 1
        Then I see url_format error message
        # Currently we are working with 1st field. It means, that if 1st field
        # contain incorrect value, 2nd and 3rd fields should be disabled until
        # 1st field will be filled by correct correct value
        And I expect 2, 3 inputs are disabled
        # We are not clearing fields here,
        # Because we changing same field.
        And I enter a http://youtu.be/OEoXaMPEzfM source to field number 1
        Then I do not see error message
        And I expect inputs are enabled

    #2
    Scenario: Testing interaction with test youtube server
        Given I have created a Video component with subtitles
        And I edit the component
        # first part of url will be substituted by mock_youtube_server address
        # for t__eq_exist id server will respond with transcripts
        And I enter a http://youtu.be/t__eq_exist source to field number 1
        Then I see not found status message
        # t__eq_exist subs locally not presented at this moment
        And I see import button

        # for t_not_exist id server will respond with 404
        And I enter a http://youtu.be/t_not_exist source to field number 1
        Then I see not found status message
        And I do not see import button
        And I see disabled_download_to_edit button

    #3
    Scenario: Youtube id only: check "not found" and "import" states
        Given I have created a Video component with subtitles
        And I edit the component

        # Not found: w/o local or server subs
        And I remove t_not_exist transcripts id from store
        And I enter a http://youtu.be/t_not_exist source to field number 1
        Then I see not found status message
        And I see "" value in the "HTML5 Timed Transcript" field

        # Import: w/o local but with server subs
        And I remove t__eq_exist transcripts id from store
        And I enter a http://youtu.be/t__eq_exist source to field number 1
        Then I see not found status message
        And I see import button
        And I click import button
        Then I see found status message
        And I don't see upload_new_timed_transcripts button
        And I see download_to_edit button
        And I see "t__eq_exist" value in the "HTML5 Timed Transcript" field

    #4
    Scenario: Youtube id only: check "Found" state
        Given I have created a Video component with t_not_exist subtitles
        And I edit the component

        And I enter a http://youtu.be/t_not_exist source to field number 1
        Then I see found status message
        And I see "t_not_exist" value in the "HTML5 Timed Transcript" field

    #5
    Scenario: Youtube id only: check "Found" state when user sets youtube_id with local and server subs and they are equal

        Given I have created a Video component with t__eq_exist subtitles
        And I edit the component

        And I enter a http://youtu.be/t__eq_exist source to field number 1
        And I see found status message
        And I see "t__eq_exist" value in the "HTML5 Timed Transcript" field

    #6
    Scenario: Youtube id only: check "Found" state when user sets youtube_id with local and server subs and they are not  equal
        Given I have created a Video component with t_neq_exist subtitles
        And I edit the component

        And I enter a http://youtu.be/t_neq_exist source to field number 1
        And I see replace status message
        And I see replace button
        And I click replace button
        And I see found status message
        And I see "t_neq_exist" value in the "HTML5 Timed Transcript" field

    #7
    Scenario: html5 source only: check "Not Found" state
        Given I have created a Video component
        And I edit the component

        And I enter a t_not_exist.mp4 source to field number 1
        Then I see not found status message
        And I see "" value in the "HTML5 Timed Transcript" field

    #8
    Scenario: html5 source only: check "Found" state
        Given I have created a Video component with t_not_exist subtitles
        And I edit the component

        And I enter a t_not_exist.mp4 source to field number 1
        Then I see found status message
        And I see "t_not_exist" value in the "HTML5 Timed Transcript" field

    #9
    Scenario: User sets youtube_id w/o server but with local subs and one html5 link w/o subs
        Given I have created a Video component with t_not_exist subtitles
        And I edit the component

        And I enter a http://youtu.be/t_not_exist source to field number 1
        Then I see found status message

        And I enter a test_video_name.mp4 source to field number 2
        Then I see found status message
        And I see "t_not_exist" value in the "HTML5 Timed Transcript" field

    #10
    Scenario: User sets youtube_id w/o local but with server subs and one html5 link w/o subs
        Given I have created a Video component
        And I edit the component

        And I enter a http://youtu.be/t__eq_exist source to field number 1
        Then I see not found status message
        And I see import button
        And I click import button
        Then I see found status message

        And I enter a t_not_exist.mp4 source to field number 2
        Then I see found status message
        And I see "t__eq_exist" value in the "HTML5 Timed Transcript" field

    #11
    Scenario: User sets youtube_id w/o local but with server subs and one html5 link w/o transcripts w/o import action, then another one html5 link w/o transcripts
        Given I have created a Video component
        And I edit the component

        And I enter a http://youtu.be/t__eq_exist source to field number 1
        Then I see not found status message
        And I see import button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_not_exist.mp4 source to field number 2
        Then I see not found status message
        And I see import button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_not_exist.webm source to field number 3
        Then I see not found status message
        And I see import button
        And I don't see upload_new_timed_transcripts button

    #12
    Scenario: Entering youtube (no importing), and 2 html5 sources without transcripts - "Not Found"
        Given I have created a Video component
        And I edit the component
        And I enter a http://youtu.be/t_not_exist source to field number 1
        Then I see not found status message
        And I see disabled_download_to_edit button
        And I don't see upload_new_timed_transcripts button
        And I enter a t_not_exist.mp4 source to field number 2
        Then I see not found status message
        And I don't see upload_new_timed_transcripts button
        And I see disabled_download_to_edit button
        And I enter a t_not_exist.webm source to field number 3
        Then I see not found status message
        And I see disabled_download_to_edit button
        And I don't see upload_new_timed_transcripts button

    #13
    Scenario: Entering youtube with imported transcripts, and 2 html5 sources without transcripts - "Found"
        Given I have created a Video component
        And I edit the component

        And I enter a http://youtu.be/t__eq_exist source to field number 1
        Then I see not found status message
        And I see import button
        And I click import button
        Then I see found status message
        And I don't see upload_new_timed_transcripts button

        And I enter a t_not_exist.mp4 source to field number 2
        Then I see found status message
        And I see download_to_edit button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_not_exist.webm source to field number 3
        Then I see found status message
        And I see download_to_edit button
        And I don't see upload_new_timed_transcripts button

    #14
    Scenario: Entering youtube w/o transcripts - html5 w/o transcripts - html5 with transcripts
        Given I have created a Video component with t_neq_exist subtitles
        And I edit the component

        And I enter a http://youtu.be/t_not_exist source to field number 1
        Then I see not found status message
        And I see disabled_download_to_edit button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_not_exist.mp4 source to field number 2
        Then I see not found status message
        And I see disabled_download_to_edit button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_neq_exist.webm source to field number 3
        Then I see found status message
        And I see download_to_edit button
        And I don't see upload_new_timed_transcripts button

    #15
    Scenario: Entering youtube w/o imported transcripts - html5 w/o transcripts w/o import - html5 with transcripts
        Given I have created a Video component with t_neq_exist subtitles
        And I edit the component

        And I enter a http://youtu.be/t__eq_exist source to field number 1
        Then I see not found status message
        And I see import button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_not_exist.mp4 source to field number 2
        Then I see not found status message
        And I see import button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_neq_exist.webm source to field number 3
        Then I see not found status message
        And I see import button
        And I don't see upload_new_timed_transcripts button

    #16
    Scenario: Entering youtube w/o imported transcripts - html5 with transcripts - html5 w/o transcripts w/o import
        Given I have created a Video component with t_neq_exist subtitles
        And I edit the component

        And I enter a http://youtu.be/t__eq_exist source to field number 1
        Then I see not found status message
        And I see import button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_neq_exist.mp4 source to field number 2
        Then I see not found status message
        And I see import button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_not_exist.webm source to field number 3
        Then I see not found status message
        And I see import button
        And I don't see upload_new_timed_transcripts button

    #17
    Scenario: Entering youtube with imported transcripts - html5 with transcripts - html5 w/o transcripts
        Given I have created a Video component with t_neq_exist subtitles
        And I edit the component

        And I enter a http://youtu.be/t__eq_exist source to field number 1
        Then I see not found status message
        And I see import button
        And I click import button
        Then I see found status message
        And I don't see upload_new_timed_transcripts button

        And I enter a t_neq_exist.mp4 source to field number 2
        Then I see found status message
        And I see download_to_edit button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_not_exist.webm source to field number 3
        Then I see found status message
        And I see download_to_edit button
        And I don't see upload_new_timed_transcripts button

    #18
    Scenario: Entering youtube with imported transcripts - html5 w/o transcripts - html5 with transcripts
        Given I have created a Video component with t_neq_exist subtitles
        And I edit the component

        And I enter a http://youtu.be/t__eq_exist source to field number 1
        Then I see not found status message
        And I see import button
        And I click import button
        Then I see found status message
        And I don't see upload_new_timed_transcripts button

        And I enter a t_not_exist.mp4 source to field number 2
        Then I see found status message
        And I see download_to_edit button
        And I don't see upload_new_timed_transcripts button

        And I enter a t_neq_exist.webm source to field number 3
        Then I see found status message
        And I see download_to_edit button
        And I don't see upload_new_timed_transcripts button

    #19
    Scenario: Entering html5 with transcripts - upload - youtube w/o transcripts
        Given I have created a Video component with t__eq_exist subtitles
        And I edit the component

        And I enter a t__eq_exist.mp4 source to field number 1
        Then I see found status message
        And I see download_to_edit button
        And I see upload_new_timed_transcripts button
        And I upload the transcripts file "test_transcripts.srt"
        Then I see uploaded_successfully status message
        And I see download_to_edit button
        And I see upload_new_timed_transcripts button
        And I see "test_transcripts" value in the "HTML5 Timed Transcript" field

        And I enter a http://youtu.be/t_not_exist source to field number 2
        Then I see found status message
        And I see download_to_edit button
        And I don't see upload_new_timed_transcripts button

        And I enter a test_transcripts.mp4 source to field number 3
        Then I see found status message

    #20
    Scenario: Enter 2 HTML5 sources with transcripts, they are not the same, choose
        Given I have created a Video component with t_not_exist subtitles
        And I edit the component

        And I enter a test_transcripts.mp4 source to field number 1
        Then I see not found status message
        And I see download_to_edit button
        And I see upload_new_timed_transcripts button
        And I upload the transcripts file "test_transcripts.srt"
        Then I see uploaded_successfully status message
        And I see "test_transcripts" value in the "HTML5 Timed Transcript" field

        And I enter a t_not_exist.webm source to field number 2
        Then I see replace status message

        And I see choose button test_transcripts.mp4 number 1
        And I see choose button t_not_exist.webm number 2
        And I click choose button number 2
        And I see "t_not_exist" value in the "HTML5 Timed Transcript" field
