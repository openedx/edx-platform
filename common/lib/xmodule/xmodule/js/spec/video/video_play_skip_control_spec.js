(function (WAIT_TIMEOUT) {
    'use strict';

    describe('VideoPlaySkipControl', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').andReturn(null);
            state = jasmine.initializePlayer('video_with_bumper.html').bumperState;
            spyOn(state.videoCommands, 'execute');
        });

        afterEach(function () {
            $('source').remove();
            state.storage.clear();
            state.videoPlayer.destroy();
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
            expect($('.video_control.play')).not.toExist();
            expect($('.video_control.skip')).toExist();
        });

        it('can start video playing on click', function () {
            $('.video_control.play').click();
            expect(state.videoCommands.execute).toHaveBeenCalledWith('play');
        });

        it('can skip the video on click', function () {
            state.el.trigger('play');
            spyOn(state.videoPlayer, 'isPlaying').andReturn(true);
            $('.video_control.skip').first().click();
            expect(state.videoCommands.execute).toHaveBeenCalledWith('skip');
        });

        it('can destroy itself', function () {
            var plugin = state.videoPlaySkipControl,
                el = plugin.el;
            spyOn($.fn, 'off').andCallThrough();
            state.videoPlaySkipControl.destroy();
            expect(state.videoPlaySkipControl).toBeUndefined();
            expect(el).not.toExist();
            expect($.fn.off).toHaveBeenCalledWith('destroy', plugin.destroy);
        });

    });
}).call(this, window.WAIT_TIMEOUT);
