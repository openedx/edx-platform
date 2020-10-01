(function() {
    'use strict';
    describe('VideoPlayer completion', function() {
        var state, oldOTBD, completionAjaxCall, time;

        beforeEach(function() {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice')
                .and.returnValue(null);

            state = jasmine.initializePlayer({
                recordedYoutubeIsAvailable: true,
                completionEnabled: true,
                publishCompletionUrl: 'https://example.com/publish_completion_url'
            });
            state.completionHandler.completeAfterTime = 20;

            completionAjaxCall = {
                url: state.config.publishCompletionUrl,
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json',
                data: JSON.stringify({completion: 1.0}),
                success: jasmine.any(Function),
                error: jasmine.any(Function)
            };
        });

        afterEach(function() {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
            state.storage.clear();
            if (state.videoPlayer) {
                state.videoPlayer.destroy();
            }
        });

        it('calls the completion api when marking an object complete', function() {
            state.completionHandler.markCompletion(Date.now());
            expect($.ajax).toHaveBeenCalledWith(completionAjaxCall);
            expect(state.completionHandler.isComplete).toEqual(true);
        });

        it('calls the completion api on the LMS when the time updates', function() {
            spyOn(state.completionHandler, 'markCompletion').and.callThrough();
            state.el.trigger('timeupdate', 24.0);
            expect(state.completionHandler.markCompletion).toHaveBeenCalled();
            state.completionHandler.markCompletion.calls.reset();
            // But the handler is not called again after the block is completed.
            state.el.trigger('timeupdate', 30.0);
            expect(state.completionHandler.markCompletion).not.toHaveBeenCalled();
        });

        it('does not call the completion api on the LMS when the video is loaded but not seen', function() {
            spyOn(window, 'VerticalStudentView').and.callThrough();
            // The VerticalStudentView object is created to kick off the function that checks if
            // each vertical is completable by viewing, and, if so, sends an ajax call to mark completion
            // eslint-disable-next-line no-new
            new window.VerticalStudentView(null, '#video_example');
            expect(window.VerticalStudentView).toHaveBeenCalled();
            expect($.ajax).not.toHaveBeenCalledWith(completionAjaxCall);
        });

        it('calls the completion api on the LMS when the video ends', function() {
            spyOn(state.completionHandler, 'markCompletion').and.callThrough();
            state.el.trigger('ended');
            expect(state.completionHandler.markCompletion).toHaveBeenCalled();
        });

        it('triggers progress', function(done) {
            var duration = 0;
            jasmine.waitUntil(function() {
                duration = state.videoPlayer.duration();
                return duration > 0;
            }).then(function() {
                spyOn(state.completionHandler, 'computeProgress').and.callThrough();
                spyOn(state.completionHandler, 'triggerProgress').and.callThrough();
                // 4 percents should be equivalent to 0
                time = 4 * duration / 100;
                state.el.trigger('timeupdate', time);
                expect(state.completionHandler.computeProgress).toHaveBeenCalled();
                expect(state.completionHandler.triggerProgress).toHaveBeenCalled();
                state.completionHandler.computeProgress.calls.reset();
                state.completionHandler.triggerProgress.calls.reset();
                // 8 percents should be equivalent to 5
                time = 8 * duration / 100;
                state.el.trigger('timeupdate', time);
                expect(state.completionHandler.computeProgress).toHaveBeenCalled();
                expect(state.completionHandler.triggerProgress).toHaveBeenCalled();
                state.completionHandler.computeProgress.calls.reset();
                state.completionHandler.triggerProgress.calls.reset();
                // Another timeupdate in the same 5-range should not trigger "triggerProgress"
                time = 9 * duration / 100;
                state.el.trigger('timeupdate', time);
                expect(state.completionHandler.computeProgress).toHaveBeenCalled();
                expect(state.completionHandler.triggerProgress).not.toHaveBeenCalled();
            }).always(done);
        });
    });
}).call(this);
