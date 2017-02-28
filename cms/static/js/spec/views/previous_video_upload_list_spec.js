define(
    ['jquery', 'underscore', 'backbone', 'js/views/previous_video_upload_list',
     'common/js/spec_helpers/template_helpers', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
     'js/collections/video'],
    function($, _, Backbone, PreviousVideoUploadListView, TemplateHelpers, AjaxHelpers,
        VideoPagingCollection) {
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
                    var collection = new VideoPagingCollection(
                        _.map(
                            _.range(numModels),
                            function(num, index) {
                                return new Backbone.Model(
                                    _.extend({}, modelData, {edx_video_id: 'dummy_id_' + index})
                                );
                            }
                        ), {
                            url: videoHandlerUrl,
                            pageSize: 10,
                            sortField: "Name",
                            totalCount: numModels,
                            sortDir: "asc"
                        }
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

            describe('PagingPreviousVideoUploadListView', function() {

                var videoView, collection;
                beforeEach(function() {
                    collection = new VideoPagingCollection([
                            {
                                'client_video_id': 'foo.mp4',
                                'duration': 42,
                                'created': '2014-11-25T23:13:05',
                                'edx_video_id': 'dummy_id_1',
                                'status': 'uploading'
                            },
                            {
                                'client_video_id': 'foo.mp4',
                                'duration': 42,
                                'created': '2014-11-25T23:13:05',
                                'edx_video_id': 'dummy_id_2',
                                'status': 'uploading'
                            }
                        ],
                        {
                            url: videoHandlerUrl,
                            pageSize: 2,
                            sortField: 'Name',
                            totalCount: 3,
                            sortDir: 'asc'
                        }
                    );
                    videoView = new PreviousVideoUploadListView({
                        collection: collection,
                        videoHandlerUrl: videoHandlerUrl
                    });

                    videoView.render();
                });

                var firstPageResults = {
                        sort: 'uploadDate',
                        end: 1,
                        results: [
                            {
                                'client_video_id': 'foo.mp4',
                                'duration': 42,
                                'created': '2014-11-25T23:13:05',
                                'edx_video_id': 'dummy_id_1',
                                'status': 'uploading'
                            },
                            {
                                'client_video_id': 'foo.mp4',
                                'duration': 42,
                                'created': '2014-11-25T23:13:05',
                                'edx_video_id': 'dummy_id_2',
                                'status': 'uploading'
                            }
                        ],
                        pageSize: 2,
                        totalCount: 3,
                        start: 0,
                        page: 0
                    }, secondPageResults = {
                        sort: 'uploadDate',
                        end: 2,
                        results: [
                            {
                                'client_video_id': 'foo.mp4',
                                'duration': 42,
                                'created': '2014-11-25T23:13:05',
                                'edx_video_id': 'dummy_id_3',
                                'status': 'uploading'
                            }
                        ],
                        pageSize: 2,
                        totalCount: 3,
                        start: 2,
                        page: 1
                    };

                it('can move forward a page using the next page button', function() {
                    var requests = AjaxHelpers.requests(this);
                    expect(videoView.pagingView.pagingFooter).toBeDefined();
                    expect(videoView.pagingView.pagingFooter.$('button.next-page-link'))
                        .not.toHaveClass('is-disabled');
                    videoView.pagingView.pagingFooter.$('button.next-page-link').click();
                    AjaxHelpers.respondWithJson(requests, secondPageResults);
                    expect(videoView.pagingView.pagingFooter.$('button.next-page-link'))
                        .toHaveClass('is-disabled');
                });

                it('can move back a page using the previous page button', function() {
                    var requests = AjaxHelpers.requests(this);
                    videoView.pagingView.setPage(2);
                    AjaxHelpers.respondWithJson(requests, secondPageResults);
                    expect(videoView.pagingView.pagingFooter).toBeDefined();
                    expect(videoView.pagingView.pagingFooter.$('button.previous-page-link'))
                        .not.toHaveClass('is-disabled');
                    videoView.pagingView.pagingFooter.$('button.previous-page-link').click();
                    AjaxHelpers.respondWithJson(requests, firstPageResults);
                    expect(videoView.pagingView.pagingFooter.$('button.previous-page-link'))
                        .toHaveClass('is-disabled');
                });

                it('can set the current page using the page number input', function() {
                    var requests = AjaxHelpers.requests(this);
                    videoView.pagingView.setPage(1);
                    AjaxHelpers.respondWithJson(requests, firstPageResults);
                    videoView.pagingView.pagingFooter.$('#page-number-input').val('2');
                    videoView.pagingView.pagingFooter.$('#page-number-input').trigger('change');
                    AjaxHelpers.respondWithJson(requests, secondPageResults);
                    expect(videoView.collection.getPageNumber()).toBe(2);
                    expect(videoView.pagingView.pagingFooter.$('button.previous-page-link'))
                        .not.toHaveClass('is-disabled');
                });
            });
        });
    }
);
