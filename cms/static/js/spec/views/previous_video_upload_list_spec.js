define(
    ['jquery', 'underscore', 'backbone', 'js/views/previous_video_upload_list',
     'common/js/spec_helpers/template_helpers', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'],
    function($, _, Backbone, PreviousVideoUploadListView, TemplateHelpers, AjaxHelpers) {
        'use strict';
        describe('PreviousVideoUploadListView', function() {
            var videoHandlerUrl = '/videos/course-v1:org.0+course_0+Run_0',
                render = function(numModels) {
                    var modelData = {
                        client_video_id: 'foo.mp4',
                        duration: 42,
                        created: '2014-11-25T23:13:05',
                        edx_video_id: 'dummy_id',
                        status: 'uploading'
                    };
                    var collection = new Backbone.Collection(
                        _.map(
                            _.range(numModels),
                            function(num, index) {
                                return new Backbone.Model(
                                    _.extend({}, modelData, {edx_video_id: 'dummy_id_' + index})
                                );
                            }
                        )
                    );
                    var view = new PreviousVideoUploadListView({
                        collection: collection,
                        videoHandlerUrl: videoHandlerUrl
                    });
                    return view.render().$el;
                },
                verifyVideosInfo;

            beforeEach(function() {
                setFixtures('<div id="page-prompt"></div>');
                TemplateHelpers.installTemplate('previous-video-upload');
                TemplateHelpers.installTemplate('previous-video-upload-list');
            });

            verifyVideosInfo = function(test, confirmRemove) {
                var firstVideo,
                    numVideos = 5,
                    $el = render(numVideos),
                    firstVideoId = 'dummy_id_0',
                    requests = AjaxHelpers.requests(test),
                    firstVideoSelector = '.js-table-body tr:first-child';

                // total number of videos should be 5 before remove
                expect($el.find('.js-table-body tr').length).toEqual(numVideos);

                // get first video element
                firstVideo = $el.find(firstVideoSelector);

                // verify first video id before removal
                expect(firstVideo.find('.video-id-col').text()).toEqual(firstVideoId);

                // remove first video in the table
                firstVideo.find('.remove-video-button.action-button').click();

                if (confirmRemove) {
                    // click on Remove button on confirmation popup
                    $('.action-primary').click();
                    AjaxHelpers.expectJsonRequest(requests, 'DELETE', videoHandlerUrl + '/dummy_id_0');
                    AjaxHelpers.respondWithNoContent(requests);
                    numVideos -= 1;
                    firstVideoId = 'dummy_id_1';
                } else {
                    // click on Cancel button on confirmation popup
                    $('.action-secondary').click();
                    expect(requests.length).toEqual(0);
                }

                // verify total number of videos after Remove/Cancel
                expect($el.find('.js-table-body tr').length).toEqual(numVideos);

                // verify first video id after Remove/Cancel
                firstVideo = $el.find(firstVideoSelector);
                expect(firstVideo.find('.video-id-col').text()).toEqual(firstVideoId);
            };

            it('should render an empty collection', function() {
                var $el = render(0);
                expect($el.find('.js-table-body').length).toEqual(1);
                expect($el.find('.js-table-body tr').length).toEqual(0);
            });

            it('should render a non-empty collection', function() {
                var $el = render(5);
                expect($el.find('.js-table-body').length).toEqual(1);
                expect($el.find('.js-table-body tr').length).toEqual(5);
            });

            it('removes video upon click on Remove button', function() {
                // Remove a video from list and verify that correct video is removed
                verifyVideosInfo(this, true);
            });

            it('does nothing upon click on Cancel button', function() {
                // Verify that nothing changes when we click on Cancel button on confirmation popup
                verifyVideosInfo(this, false);
            });
        });
    }
);
