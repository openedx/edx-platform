(function() {
    'use strict';
    describe('VideoPlayer completion', function() {
        var state, oldOTBD;

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
            expect($.ajax).toHaveBeenCalledWith({
                url: state.config.publishCompletionUrl,
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json',
                data: JSON.stringify({completion: 1.0}),
                success: jasmine.any(Function),
                error: jasmine.any(Function)
            });
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

        it('calls the completion api on the LMS when the video ends', function() {
            spyOn(state.completionHandler, 'markCompletion').and.callThrough();
            state.el.trigger('ended');
            expect(state.completionHandler.markCompletion).toHaveBeenCalled();
        });
    });
}).call(this);
