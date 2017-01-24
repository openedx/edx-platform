(function() {
    'use strict';
    describe('VideoSkipControl', function() {
        var state, oldOTBD;

        beforeEach(function() {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').and.returnValue(null);
            state = jasmine.initializePlayer('video_with_bumper.html');
            $('.poster .btn-play').click();
            spyOn(state.bumperState.videoCommands, 'execute').and.callThrough();
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

        it('can render the control when video starts playing', function() {
            expect($('.skip-control')).not.toExist();
            state.el.trigger('play');
            expect($('.skip-control')).toExist();
        });

        it('can skip the video on click', function() {
            spyOn(state.bumperState.videoBumper, 'skipAndDoNotShowAgain');
            state.el.trigger('play');
            $('.skip-control').click();
            expect(state.bumperState.videoCommands.execute).toHaveBeenCalledWith('skip', true);
            expect(state.bumperState.videoBumper.skipAndDoNotShowAgain).toHaveBeenCalled();
        });

        it('can destroy itself', function() {
            state.bumperState.videoPlaySkipControl.destroy();
            expect(state.bumperState.videoPlaySkipControl).toBeUndefined();
        });
    });
}).call(this);
