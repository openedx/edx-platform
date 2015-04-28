(function (WAIT_TIMEOUT) {
    'use strict';

    describe('VideoSkipControl', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').andReturn(null);
            state = jasmine.initializePlayer('video_with_bumper.html');
            spyOn(state.bumperState.videoCommands, 'execute');
        });

        afterEach(function () {
            $('source').remove();
            state.storage.clear();
            if (state.bumperState.vodeoPlayer) {
                state.bumperState.videoPlayer.destroy();
            }
            if (state.vodeoPlayer) {
                state.videoPlayer.destroy();
            }
            window.onTouchBasedDevice = oldOTBD;
        });

        it('can render the control when video starts playing', function () {
            expect($('.skip-control')).not.toExist();
            state.el.trigger('play');
            expect($('.skip-control')).toExist();
        });

        it('add ARIA attributes to play control', function () {
            state.el.trigger('play');
            expect($('.skip-control')).toHaveAttrs({
                'role': 'button',
                'title': 'Do not show again',
                'aria-disabled': 'false'
            });
        });

        it('can skip the video on click', function () {
            state.el.trigger('play');
            $('.skip-control').click();
            expect(state.bumperState.videoCommands.execute).toHaveBeenCalledWith('skip', true);
        });

        it('can destroy itself', function () {
            state.bumperState.videoPlaySkipControl.destroy();
            expect(state.bumperState.videoPlaySkipControl).toBeUndefined();
        });

    });
}).call(this, window.WAIT_TIMEOUT);
