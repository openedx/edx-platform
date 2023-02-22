define(
    ['jquery', 'underscore', 'backbone', 'js/views/video_transcripts', 'js/views/previous_video_upload_list',
        'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers', 'common/js/spec_helpers/template_helpers'],
    function($, _, Backbone, VideoTranscriptsView, PreviousVideoUploadListView, AjaxHelpers, TemplateHelpers) {
        'use strict';
        describe('VideoTranscriptsView', function() {
            var videoTranscriptsView,
                renderView,
                verifyTranscriptStateInfo,
                verifyMessage,
                verifyDetailedErrorMessage,
                createFakeTranscriptFile,
                transcripts = ['en', 'es', 'ur'],
                edxVideoID = 'test-edx-video-id',
                clientVideoID = 'Video client title name.mp4',
                transcriptAvailableLanguages = [
                    {
                        language_code: 'en',
                        language_text: 'English'
                    },
                    {
                        language_code: 'es',
                        language_text: 'Spanish'
                    },
                    {
                        language_code: 'ar',
                        language_text: 'Chinese'
                    },
                    {
                        language_code: 'ur',
                        language_text: 'Urdu'
                    }
                ],
                TRANSCRIPT_DOWNLOAD_FILE_FORMAT = 'srt',
                TRANSCRIPT_DOWNLOAD_URL = 'abc.com/transcript_download/course_id',
                TRANSCRIPT_UPLOAD_URL = 'abc.com/transcript_upload/course_id',
                TRANSCRIPT_DELETE_URL = 'abc.com/transcript_delete/course_id',
                videoSupportedFileFormats = ['.mov', '.mp4'],
                videoTranscriptSettings = {
                    trancript_download_file_format: TRANSCRIPT_DOWNLOAD_FILE_FORMAT,
                    transcript_download_handler_url: TRANSCRIPT_DOWNLOAD_URL,
                    transcript_upload_handler_url: TRANSCRIPT_UPLOAD_URL,
                    transcript_delete_handler_url: TRANSCRIPT_DELETE_URL
                },
                videoListView;

            verifyTranscriptStateInfo = function($transcriptEl, transcriptLanguage) {
                var $transcriptActionsEl = $transcriptEl.find('.transcript-actions'),
                    downloadTranscriptActionEl = $transcriptActionsEl.find('.download-transcript-button'),
                    uploadTranscriptActionEl = $transcriptActionsEl.find('.upload-transcript-button');

                // Verify transcript data attributes
                expect($transcriptEl.data('edx-video-id')).toEqual(edxVideoID);
                expect($transcriptEl.data('language-code')).toEqual(transcriptLanguage);

                // Verify transcript language dropdown has correct value set.
                expect($transcriptEl.find('.transcript-language-menu').val(), transcriptLanguage);

                // Verify transcript actions
                expect(downloadTranscriptActionEl.html().trim(), 'Download');
                expect(
                    downloadTranscriptActionEl.attr('href'),
                    TRANSCRIPT_DOWNLOAD_URL + '?edx_video_id=' + edxVideoID + '&language_code=' + transcriptLanguage
                );

                expect(uploadTranscriptActionEl.html().trim(), 'Replace');
            };

            verifyMessage = function($transcriptEl, status) {
                var $transcriptStatusEl = $transcriptEl.find('.transcript-upload-status-container'),
                    statusData = videoTranscriptsView.transcriptUploadStatuses[status];

                expect($transcriptStatusEl.hasClass(statusData.statusClass)).toEqual(true);
                expect($transcriptStatusEl.find('span.fa').hasClass(statusData.iconClasses)).toEqual(true);
                expect(
                    $transcriptStatusEl.find('.more-details-action').hasClass('hidden')
                ).toEqual(statusData.hiddenClass === 'hidden');
                expect(
                    $transcriptStatusEl.find('.transcript-detail-status').html().trim()
                ).toEqual(statusData.shortMessage);
            };

            verifyDetailedErrorMessage = function($transcriptEl, expectedTitle, expectedMessage) {
                $transcriptEl.find('.more-details-action').click();
                expect($('#prompt-warning-title').text().trim()).toEqual(expectedTitle);
                expect($('#prompt-warning-description').text().trim()).toEqual(expectedMessage);
            };

            createFakeTranscriptFile = function(transcriptFileName) {
                var transcriptFileName = transcriptFileName || 'test-transcript.srt',   // eslint-disable-line no-redeclare, max-len
                    size = 100,
                    type = '';
                return new File([new Blob([Array(size).join('i')], {type: type})], transcriptFileName);
            };

            renderView = function(availableTranscripts) {
                var videoViewIndex = 0,
                    videoData = {
                        client_video_id: clientVideoID,
                        edx_video_id: edxVideoID,
                        created: '2014-11-25T23:13:05',
                        transcripts: availableTranscripts
                    },
                    videoCollection = new Backbone.Collection([new Backbone.Model(videoData)]);

                videoListView = new PreviousVideoUploadListView({
                    collection: videoCollection,
                    videoImageSettings: {},
                    videoTranscriptSettings: videoTranscriptSettings,
                    transcriptAvailableLanguages: transcriptAvailableLanguages,
                    videoSupportedFileFormats: videoSupportedFileFormats
                });
                videoListView.setElement($('.wrapper-assets'));
                videoListView.render();

                videoTranscriptsView = videoListView.itemViews[videoViewIndex].videoTranscriptsView;
            };

            beforeEach(function() {
                setFixtures(
                    '<div id="page-prompt"></div>' +
                    '<div id="page-notification"></div>' +
                    '<section class="wrapper-assets"></section>'
                );
                TemplateHelpers.installTemplate('previous-video-upload-list');
                renderView(transcripts);
            });

            it('renders as expected', function() {
                // Verify transcript container is present.
                expect(videoListView.$el.find('.video-transcripts-header')).toExist();
                // Veirfy transcript column header is present.
                expect(videoListView.$el.find('.js-table-head .video-head-col.transcripts-col')).toExist();
                // Verify transcript data column is present.
                expect(videoListView.$el.find('.js-table-body .transcripts-col')).toExist();
                // Verify view has initiallized.
                expect(_.isUndefined(videoTranscriptsView)).toEqual(false);
            });

            it('does not show list of transcripts initially', function() {
                expect(
                    videoTranscriptsView.$el.find('.video-transcripts-wrapper').hasClass('hidden')
                ).toEqual(true);
                expect(videoTranscriptsView.$el.find('.toggle-show-transcripts-button-text').html().trim()).toEqual(
                    'Show transcripts (' + transcripts.length + ')'
                );
            });

            it('shows list of transcripts when clicked on show transcript button', function() {
                // Verify transcript container is hidden
                expect(
                    videoTranscriptsView.$el.find('.video-transcripts-wrapper').hasClass('hidden')
                ).toEqual(true);

                // Verify initial button text
                expect(videoTranscriptsView.$el.find('.toggle-show-transcripts-button-text').html().trim()).toEqual(
                    'Show transcripts (' + transcripts.length + ')'
                );
                videoTranscriptsView.$el.find('.toggle-show-transcripts-button').click();

                // Verify transcript container is not hidden
                expect(
                    videoTranscriptsView.$el.find('.video-transcripts-wrapper').hasClass('hidden')
                ).toEqual(false);

                // Verify button text is changed.
                expect(videoTranscriptsView.$el.find('.toggle-show-transcripts-button-text').html().trim()).toEqual(
                    'Hide transcripts (' + transcripts.length + ')'
                );
            });

            it('hides list of transcripts when clicked on hide transcripts button', function() {
                // Click to show transcripts first.
                videoTranscriptsView.$el.find('.toggle-show-transcripts-button').click();

                // Verify button text.
                expect(videoTranscriptsView.$el.find('.toggle-show-transcripts-button-text').html().trim()).toEqual(
                    'Hide transcripts (' + transcripts.length + ')'
                );

                // Verify transcript container is not hidden
                expect(
                    videoTranscriptsView.$el.find('.video-transcripts-wrapper').hasClass('hidden')
                ).toEqual(false);

                videoTranscriptsView.$el.find('.toggle-show-transcripts-button').click();

                // Verify button text is changed.
                expect(videoTranscriptsView.$el.find('.toggle-show-transcripts-button-text').html().trim()).toEqual(
                    'Show transcripts (' + transcripts.length + ')'
                );

                // Verify transcript container is hidden
                expect(
                    videoTranscriptsView.$el.find('.video-transcripts-wrapper').hasClass('hidden')
                ).toEqual(true);
            });

            it('renders appropriate text when no transcript is available', function() {
                // Render view with no transcripts
                renderView({});

                // Verify appropriate text is shown
                expect(
                    videoTranscriptsView.$el.find('.transcripts-empty-text').html()
                ).toEqual('No transcript uploaded.');
            });

            it('renders correct transcript attributes', function() {
                var $transcriptEl;
                // Show transcripts
                videoTranscriptsView.$el.find('.toggle-show-transcripts-button').click();
                expect(videoTranscriptsView.$el.find('.video-transcript-content').length).toEqual(
                    transcripts.length
                );

                _.each(transcripts, function(languageCode) {
                    $transcriptEl = videoTranscriptsView.$el.find('.video-transcript-content[data-language-code="' + languageCode + '"]');  // eslint-disable-line max-len
                    // Verify correct transcript title is set.
                    expect($transcriptEl.find('.transcript-title').html()).toEqual(
                        'Video client title n_' + languageCode + '.' + TRANSCRIPT_DOWNLOAD_FILE_FORMAT
                    );
                    // Verify transcript is rendered with correct info.
                    verifyTranscriptStateInfo($transcriptEl, languageCode);
                });
            });

            it('can upload transcript', function() {
                var languageCode = 'en',
                    newLanguageCode = 'ar',
                    requests = AjaxHelpers.requests(this),
                    $transcriptEl = videoTranscriptsView.$el.find('.video-transcript-content[data-language-code="' + languageCode + '"]'); // eslint-disable-line max-len

                // Verify correct transcript title is set.
                expect($transcriptEl.find('.transcript-title').html()).toEqual(
                    'Video client title n_' + languageCode + '.' + TRANSCRIPT_DOWNLOAD_FILE_FORMAT
                );

                // Select a language
                $transcriptEl.find('.transcript-language-menu').val(newLanguageCode);

                $transcriptEl.find('.upload-transcript-button').click();

                // Add transcript to upload queue and send POST request to upload transcript.
                $transcriptEl.find('.upload-transcript-input').fileupload('add', {files: [createFakeTranscriptFile()]});

                // Verify if POST request received for transcript upload
                AjaxHelpers.expectRequest(
                    requests,
                    'POST',
                    TRANSCRIPT_UPLOAD_URL
                );

                // Send successful upload response
                AjaxHelpers.respondWithJson(requests, {});

                // Verify correct transcript title is set.
                expect($transcriptEl.find('.transcript-title').html()).toEqual(
                    'Video client title n_' + newLanguageCode + '.' + TRANSCRIPT_DOWNLOAD_FILE_FORMAT
                );

                verifyMessage($transcriptEl, 'uploaded');

                // Verify transcript is rendered with correct info.
                verifyTranscriptStateInfo($transcriptEl, newLanguageCode);
            });

            it('can delete transcript', function() {
                var languageCode = 'en',
                    requests = AjaxHelpers.requests(this),
                    $transcriptEl = videoTranscriptsView.$el.find('.video-transcript-content[data-language-code="' + languageCode + '"]'); // eslint-disable-line max-len

                // Verify correct transcript title is set.
                expect($transcriptEl.find('.transcript-title').html()).toEqual(
                    'Video client title n_' + languageCode + '.' + TRANSCRIPT_DOWNLOAD_FILE_FORMAT
                );

                $transcriptEl.find('.delete-transcript-button').click();

                // Click remove button on prompt.
                $('#page-prompt .action-primary').click();

                // Verify if DELETE request received for transcript delete
                AjaxHelpers.expectRequest(
                    requests,
                    'DELETE',
                    TRANSCRIPT_DELETE_URL + '/' + edxVideoID + '/' + languageCode
                );

                // Send successful delete response
                AjaxHelpers.respondWithJson(requests, {});

                // Verify English transcript is not present.
                expect(videoTranscriptsView.$el.find(
                    '.video-transcript-content[data-language-code="' + languageCode + '"]'
                )).not.toExist();

                // Verify transcripts view is rendered with transcript deleted for English.
                expect(videoTranscriptsView.$el.find('.toggle-show-transcripts-button-text').html().trim()).toEqual(
                    'Show transcripts (2)'
                );
            });

            it('should show error message when deleting a transcript in case of server error', function() {
                var languageCode = 'en',
                    requests = AjaxHelpers.requests(this),
                    $transcriptEl = videoTranscriptsView.$el.find('.video-transcript-content[data-language-code="' + languageCode + '"]'); // eslint-disable-line max-len

                // Verify correct transcript title is set.
                expect($transcriptEl.find('.transcript-title').html()).toEqual(
                    'Video client title n_' + languageCode + '.' + TRANSCRIPT_DOWNLOAD_FILE_FORMAT
                );

                $transcriptEl.find('.delete-transcript-button').click();

                // Verify prompt title and description.

                expect($('#page-prompt #prompt-warning-title').html().trim()).toEqual(
                    'Are you sure you want to remove this transcript?'
                );

                expect($('#page-prompt #prompt-warning-description').html().trim()).toEqual(
                    'If you remove this transcript, the transcript will not be available for any components that use this video.'   // eslint-disable-line max-len
                );

                // Click remove button on prompt.
                $('#page-prompt .action-primary').click();

                // Verify if DELETE request received for transcript delete.
                AjaxHelpers.expectRequest(
                    requests,
                    'DELETE',
                    TRANSCRIPT_DELETE_URL + '/' + edxVideoID + '/' + languageCode
                );

                AjaxHelpers.respondWithError(requests, 500);

                // Verify prompt message is shown.
                expect($('#page-notification #notification-error-title').html()).toEqual(
                    "Studio's having trouble saving your work"
                );

                // Verify English transcript container is not removed.
                expect(videoTranscriptsView.$el.find(
                    '.video-transcript-content[data-language-code="' + languageCode + '"]'
                )).toExist();

                // Verify transcripts count is correct.
                expect(videoTranscriptsView.$el.find('.toggle-show-transcripts-button-text').html().trim()).toEqual(
                    'Show transcripts (3)'
                );
            });

            it('shows error state correctly', function() {
                var languageCode = 'en',
                    requests = AjaxHelpers.requests(this),
                    errorMessage = 'Transcript failed error message',
                    $transcriptEl = videoTranscriptsView.$el.find('.video-transcript-content[data-language-code="' + languageCode + '"]'); // eslint-disable-line max-len

                $transcriptEl.find('.upload-transcript-button').click();

                // Add transcript to upload queue and send POST request to upload transcript.
                $transcriptEl.find('.upload-transcript-input').fileupload('add', {files: [createFakeTranscriptFile()]});

                // Server response with bad request.
                AjaxHelpers.respondWithError(requests, 400, {error: errorMessage});

                verifyMessage($transcriptEl, 'failed');

                // verify detailed error message
                verifyDetailedErrorMessage(
                    $transcriptEl,
                    videoTranscriptsView.defaultFailureTitle,
                    errorMessage
                );

                // Verify transcript is rendered with correct info.
                verifyTranscriptStateInfo($transcriptEl, languageCode);
            });

            it('should show error message in case of server error', function() {
                var languageCode = 'en',
                    requests = AjaxHelpers.requests(this),
                    $transcriptEl = videoTranscriptsView.$el.find('.video-transcript-content[data-language-code="' + languageCode + '"]'); // eslint-disable-line max-len

                $transcriptEl.find('.upload-transcript-button').click();

                // Add transcript to upload queue and send POST request to upload transcript.
                $transcriptEl.find('.upload-transcript-input').fileupload('add', {files: [createFakeTranscriptFile()]});

                AjaxHelpers.respondWithError(requests, 500);

                verifyMessage($transcriptEl, 'failed');

                // verify detailed error message
                verifyDetailedErrorMessage(
                    $transcriptEl,
                    videoTranscriptsView.defaultFailureTitle,
                    videoTranscriptsView.defaultFailureMessage
                );

                // Verify transcript is rendered with correct info.
                verifyTranscriptStateInfo($transcriptEl, languageCode);
            });

            it('should show error message in case of unsupported transcript file format', function() {
                var languageCode = 'en',
                    transcriptFileName = 'unsupported-transcript-file-format.txt',
                    errorMessage = 'This file type is not supported. Supported file type is ' + TRANSCRIPT_DOWNLOAD_FILE_FORMAT + '.',    // eslint-disable-line max-len
                    $transcriptEl = videoTranscriptsView.$el.find('.video-transcript-content[data-language-code="' + languageCode + '"]'); // eslint-disable-line max-len

                $transcriptEl.find('.upload-transcript-button').click();

                // Add transcript to upload queue and send POST request to upload transcript.
                $transcriptEl.find('.upload-transcript-input').fileupload('add', {
                    files: [createFakeTranscriptFile(transcriptFileName)]
                });

                verifyMessage($transcriptEl, 'validationFailed');

                // verify detailed error message
                verifyDetailedErrorMessage(
                    $transcriptEl,
                    videoTranscriptsView.defaultFailureTitle,
                    errorMessage
                );

                // Verify transcript is rendered with correct info.
                verifyTranscriptStateInfo($transcriptEl, languageCode);
            });
        });
    }
);
