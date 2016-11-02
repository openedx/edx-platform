(function(WAIT_TIMEOUT) {
    'use strict';
    describe('VideoPoster', function() {
        var state, oldOTBD;

        beforeEach(function() {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').and.returnValue(null);
            state = jasmine.initializePlayer('video_with_bumper.html');
        });

        afterEach(function() {
            $('source').remove();
            state.storage.clear();
            if (state.bumperState && state.bumperState.videoPlayer) {
                state.bumperState.videoPlayer.destroy();
            }
            if (state.videoPlayer) {
                state.videoPlayer.destroy();
            }
            window.onTouchBasedDevice = oldOTBD;
        });

        it('can render the poster', function() {
            expect($('.poster')).toExist();
            expect($('.btn-play')).toExist();
        });

        it('can start playing the video on click', function(done) {
            $('.btn-play').click();
            jasmine.waitUntil(function() {
                return state.el.hasClass('is-playing');
            }).done(done);
        });

        it('destroy itself on "play" event', function() {
            $('.btn-play').click();
            expect($('.poster')).not.toExist();
        });
    });
}).call(this, window.WAIT_TIMEOUT);
