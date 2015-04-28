(function (WAIT_TIMEOUT) {
    'use strict';

    describe('VideoPlaySkipControl', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').andReturn(null);

// Start the video with Bumper
            state = jasmine.initializePlayer();
            spyOn(this.state.videoCommands, 'execute');
        });

        afterEach(function () {
            $('source').remove();
            state.storage.clear();
            window.Video.previousState = null;
            window.onTouchBasedDevice = oldOTBD;
        });

        it('can render the control', function () {
            expect($('.video_control.play')).toExist();
        });

        it('add ARIA attributes to play control', function () {
            expect($('.video_control.play')).toHaveAttrs({
                'role': 'button',
                'title': 'Play',
                'aria-disabled': 'false'
            });
        });

        it('can update state on play', function () {
            state.el.trigger('play');
            // changed to `skip` button
            //... expect().toBe();
            // click on the video do not pause the video
            $('video').click();
            expect(state.videoPlayer.isPlaying()).toBeTruthy();
        });

        it('can start video playing on click', function () {
            $('.video_control.play').click();
            expect(state.videoCommands.execute).toHaveBeenCalledWith('play');
        });

        it('can skip the video on click', function () {
            state.videoPlaySkipControl.play();
            $('.video_control.skip').click();
            expect(state.videoCommands.execute).toHaveBeenCalledWith('skip');
        });

        it('can destroy itself', function () {
            expect().toBe();
        });

    });
}).call(this, window.WAIT_TIMEOUT);
