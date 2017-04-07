define(
    ['jquery', 'underscore', 'backbone', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'js/views/video_thumbnail', 'common/js/spec_helpers/template_helpers'],
    function($, _, Backbone, AjaxHelpers, VideoThumbnailView, TemplateHelpers) {
        'use strict';
        describe('VideoThumbnailView', function() {
            var IMAGE_UPLOAD_URL = '/videos/upload/image',
                UPLOADED_IMAGE_URL = 'images/upload_success.jpg',
                videoThumbnailView,
                createFakeImageFile,
                verifyStateInfo,
                render = function(modelData) {
                    var defaultData = {
                        client_video_id: 'foo.mp4',
                        duration: 42,
                        created: '2014-11-25T23:13:05',
                        edx_video_id: 'dummy_id',
                        status: 'uploading',
                        thumbnail_url: null
                    };
                    videoThumbnailView = new VideoThumbnailView({
                        model: new Backbone.Model($.extend({}, defaultData, modelData)),
                        imageUploadURL: IMAGE_UPLOAD_URL
                    });
                    return videoThumbnailView.render().$el;
                };

            createFakeImageFile = function(size) {
                var fileFakeData = 'i63ljc6giwoskyb9x5sw0169bdcmcxr3cdz8boqv0lik971972cmd6yknvcxr5sw0nvc169bdcmcxsdf';
                return new Blob(
                    [fileFakeData.substr(0, size)],
                    {type: 'image/jpg'}
                );
            };

            verifyStateInfo = function($thumbnail, state, onHover, additionalSRText) {
                var beforeIcon,
                    beforeText;

                // Verify hover message, save the text before hover to verify later
                if (onHover) {
                    beforeIcon = $thumbnail.find('.action-icon').html().trim();
                    beforeText = $thumbnail.find('.action-text').html().trim();
                    $thumbnail.trigger('mouseover');
                }

                if (additionalSRText) {
                    expect(
                        $thumbnail.find('.thumbnail-action .action-text-sr').text().trim()
                    ).toEqual(additionalSRText);
                }

                expect($thumbnail.find('.action-icon').html().trim()).toEqual(
                     videoThumbnailView.actionsInfo[state].icon
                );
                expect($thumbnail.find('.action-text').html().trim()).toEqual(
                    videoThumbnailView.actionsInfo[state].text
                );

                // Verify if messages are restored after focus moved away
                if (onHover) {
                    $thumbnail.trigger('mouseout');
                    expect($thumbnail.find('.action-icon').html().trim()).toEqual(beforeIcon);
                    expect($thumbnail.find('.action-text').html().trim()).toEqual(beforeText);
                }
            };

            beforeEach(function() {
                setFixtures('<div id="page-prompt"></div><div id="page-notification"></div>');
                TemplateHelpers.installTemplate('video-thumbnail');
            });

            it('renders as expected', function() {
                var $el = render({});
                expect($el.find('.thumbnail-wrapper')).toExist();
                expect($el.find('.upload-image-input')).toExist();
            });

            it('does not show duration if not available', function() {
                var $el = render({duration: 0});
                expect($el.find('.thumbnail-wrapper .video-duration')).not.toExist();
            });

            it('shows the duration if available', function() {
                var $el = render({}),
                    $duration = $el.find('.thumbnail-wrapper .video-duration');
                expect($duration).toExist();
                expect($duration.find('.duration-text-machine').text().trim()).toEqual('0:42');
                expect($duration.find('.duration-text-human').text().trim()).toEqual('Video duration is 42 seconds');
            });

            it('calculates duration correctly', function() {
                var durations = [
                        {duration: -1},
                        {duration: 0},
                        {duration: 0.75, machine: '0:00', humanize: ''},
                        {duration: 5, machine: '0:05', humanize: 'Video duration is 5 seconds'},
                        {duration: 103, machine: '1:43', humanize: 'Video duration is 1 minute and 43 seconds'},
                        {duration: 120, machine: '2:00', humanize: 'Video duration is 2 minutes'},
                        {duration: 500, machine: '8:20', humanize: 'Video duration is 8 minutes and 20 seconds'},
                        {duration: 7425, machine: '123:45', humanize: 'Video duration is 123 minutes and 45 seconds'}
                    ],
                    expectedDuration;

                durations.forEach(function(item) {
                    expectedDuration = videoThumbnailView.getDuration(item.duration);
                    if (item.duration <= 0) {
                        expect(expectedDuration).toEqual(null);
                    } else {
                        expect(expectedDuration.machine).toEqual(item.machine);
                        expect(expectedDuration.humanize).toEqual(item.humanize);
                    }
                });
            });

            it('can upload image', function() {
                var $el = render({}),
                    $thumbnail = $el.find('.thumbnail-wrapper'),
                    requests = AjaxHelpers.requests(this),
                    additionalSRText = videoThumbnailView.getSRText();

                videoThumbnailView.chooseFile();

                verifyStateInfo($thumbnail, 'upload');
                verifyStateInfo($thumbnail, 'requirements', true, additionalSRText);

                // Add image to upload queue and send POST request to upload image
                $el.find('.upload-image-input').fileupload('add', {files: [createFakeImageFile(60)]});

                verifyStateInfo($thumbnail, 'progress');

                // Verify if POST request received for image upload
                AjaxHelpers.expectRequest(requests, 'POST', IMAGE_UPLOAD_URL + '/dummy_id', new FormData());

                // Send successful upload response
                AjaxHelpers.respondWithJson(requests, {image_url: UPLOADED_IMAGE_URL});

                verifyStateInfo($thumbnail, 'edit', true);

                // Verify uploaded image src
                expect($thumbnail.find('img').attr('src')).toEqual(UPLOADED_IMAGE_URL);
            });

            it('shows error state correctly', function() {
                var $el = render({}),
                    $thumbnail = $el.find('.thumbnail-wrapper'),
                    requests = AjaxHelpers.requests(this);

                videoThumbnailView.chooseFile();

                // Add image to upload queue and send POST request to upload image
                $el.find('.upload-image-input').fileupload('add', {files: [createFakeImageFile(60)]});

                AjaxHelpers.respondWithError(requests, 400);

                verifyStateInfo($thumbnail, 'error');
            });

            it('should show error notification in case of server error', function() {
                var $el = render({}),
                    requests = AjaxHelpers.requests(this);

                videoThumbnailView.chooseFile();

                // Add image to upload queue and send POST request to upload image
                $el.find('.upload-image-input').fileupload('add', {files: [createFakeImageFile(60)]});

                AjaxHelpers.respondWithError(requests);

                expect($('#notification-error-title').text().trim()).toEqual(
                    "Studio's having trouble saving your work"
                );
            });

            it('calls readMessage with correct message', function() {
                spyOn(videoThumbnailView, 'readMessages');

                videoThumbnailView.imageSelected({}, {submit: function() {}});
                expect(videoThumbnailView.readMessages).toHaveBeenCalledWith(['Video image upload started']);
                videoThumbnailView.imageUploadSucceeded({}, {result: {image_url: UPLOADED_IMAGE_URL}});
                expect(videoThumbnailView.readMessages).toHaveBeenCalledWith(['Video image upload completed']);
                videoThumbnailView.imageUploadFailed();
                expect(videoThumbnailView.readMessages).toHaveBeenCalledWith(['Video image upload failed']);
            });
        });
    }
);
