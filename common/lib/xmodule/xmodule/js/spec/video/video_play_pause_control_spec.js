(function (WAIT_TIMEOUT) {
    'use strict';

    describe('VideoPlayPauseControl', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').andReturn(null);
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
            expect().toBe();
        });

        it('can update state on pause', function () {
            state.el.trigger('pause');
            expect().toBe();
        });

        it('can update state on video ends', function () {
            state.el.trigger('ended');
            expect().toBe();
        });

        it('can start video playing on click', function () {
            $('.video_control.play').click();
            expect(state.videoCommands.execute).toHaveBeenCalledWith('togglePlayback');
        });

        it('can destroy itself', function () {
            expect().toBe();
        });

    });
}).call(this, window.WAIT_TIMEOUT);
