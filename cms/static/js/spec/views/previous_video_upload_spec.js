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
                        status: 'uploading'
                    },
                    view = new PreviousVideoUploadView({
                        model: new Backbone.Model($.extend({}, defaultData, modelData)),
                        videoHandlerUrl: '/videos/course-v1:org.0+course_0+Run_0'
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

            _.each(
                [
                    {desc: 'zero as pending', seconds: 0, expected: 'Pending'},
                    {desc: 'less than one second as zero', seconds: 0.75, expected: '0:00'},
                    {desc: 'with minutes and without seconds', seconds: 900, expected: '15:00'},
                    {desc: 'with seconds and without minutes', seconds: 15, expected: '0:15'},
                    {desc: 'with minutes and seconds', seconds: 915, expected: '15:15'},
                    {desc: 'with seconds padded', seconds: 5, expected: '0:05'},
                    {desc: 'longer than an hour as many minutes', seconds: 7425, expected: '123:45'}
                ],
                function(caseInfo) {
                    it('should render duration ' + caseInfo.desc, function() {
                        var $el = render({duration: caseInfo.seconds});
                        expect($el.find('.duration-col').text()).toEqual(caseInfo.expected);
                    });
                }
            );

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
                expect($el.find('.status-col').text()).toEqual(testStatus);
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
