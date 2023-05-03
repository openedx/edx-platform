define(
    ['jquery', 'underscore', 'backbone', 'js/views/previous_video_upload', 'common/js/spec_helpers/template_helpers',
        'common/js/spec_helpers/view_helpers'],
    function($, _, Backbone, PreviousVideoUploadView, TemplateHelpers, ViewHelpers) {
        'use strict';
        describe('PreviousVideoUploadView', function() {
            var render = function(modelData) {
                var defaultData = {
                        client_video_id: 'foo.mp4',
                        duration: 42,
                        created: '2014-11-25T23:13:05',
                        edx_video_id: 'dummy_id',
                        status: 'uploading',
                        transcripts: []
                    },
                    view = new PreviousVideoUploadView({
                        model: new Backbone.Model($.extend({}, defaultData, modelData)),
                        videoHandlerUrl: '/videos/course-v1:org.0+course_0+Run_0',
                        transcriptAvailableLanguages: [],
                        videoSupportedFileFormats: [],
                        videoTranscriptSettings: {},
                        videoImageSettings: {}
                    });
                return view.render().$el;
            };

            beforeEach(function() {
                setFixtures('<div id="page-prompt"></div><div id="page-notification"></div>');
                TemplateHelpers.installTemplate('previous-video-upload', false);
            });

            it('should render video name correctly', function() {
                var testName = 'test name';
                var $el = render({client_video_id: testName});
                expect($el.find('.name-col').text()).toEqual(testName);
            });

            it('should render created timestamp correctly', function() {
                var fakeDate = 'fake formatted date';
                spyOn(Date.prototype, 'toLocaleString').and.callFake(
                    function(locales, options) {
                        expect(locales).toEqual([]);
                        expect(options.timeZone).toEqual('UTC');
                        expect(options.timeZoneName).toEqual('short');
                        return fakeDate;
                    }
                );
                var $el = render({});
                expect($el.find('.date-col').text()).toEqual(fakeDate);
            });

            it('should render video id correctly', function() {
                var testId = 'test_id';
                var $el = render({edx_video_id: testId});
                expect($el.find('.video-id-col').text()).toEqual(testId);
            });

            it('should render status correctly', function() {
                var testStatus = 'Test Status';
                var $el = render({status: testStatus});
                expect($el.find('.video-status').text()).toEqual(testStatus);
            });

            it('should render remove button correctly', function() {
                var $el = render(),
                    removeButton = $el.find('.actions-list .action-remove a.remove-video-button');

                expect(removeButton.data('tooltip')).toEqual('Remove this video');
                expect(removeButton.find('.sr').text()).toEqual('Remove foo.mp4 video');
            });

            it('shows a confirmation popup when the remove button is clicked', function() {
                var $el = render();
                $el.find('a.remove-video-button').click();
                expect($('.prompt.warning .title').text()).toEqual('Are you sure you want to remove this video from the list?');  // eslint-disable-line max-len
                expect(
                    $('.prompt.warning .message').text()
                ).toEqual(
                    'Removing a video from this list does not affect course content. Any content that uses a previously uploaded video ID continues to display in the course.'  // eslint-disable-line max-len
                );
                expect($('.prompt.warning .action-primary').text()).toEqual('Remove');
                expect($('.prompt.warning .action-secondary').text()).toEqual('Cancel');
            });

            it('shows a notification when the remove button is clicked', function() {
                var notificationSpy = ViewHelpers.createNotificationSpy(),
                    $el = render();
                $el.find('a.remove-video-button').click();
                $('.action-primary').click();
                ViewHelpers.verifyNotificationShowing(notificationSpy, /Removing/);
            });
        });
    }
);
