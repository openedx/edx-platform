(function() {
    'use strict';

    describe('VideoPlayPauseControl', function() {
        // eslint-disable-next-line no-var
        var state, oldOTBD;

        beforeEach(function() {
            oldOTBD = window.onTouchBasedDevice;
            // eslint-disable-next-line no-undef
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').and.returnValue(null);
            // eslint-disable-next-line no-undef
            state = jasmine.initializePlayer();
            // eslint-disable-next-line no-undef
            spyOn(state.videoCommands, 'execute');
            // eslint-disable-next-line no-undef
            spyOn(state.videoSaveStatePlugin, 'saveState');
        });

        afterEach(function() {
            $('source').remove();
            state.storage.clear();
            state.videoPlayer.destroy();
            window.onTouchBasedDevice = oldOTBD;
        });

        it('can render the control', function() {
            expect($('.video_control.play')).toExist();
        });

        it('add ARIA attributes to play control', function() {
            expect($('.video_control.play')).toHaveAttrs({
                'aria-disabled': 'false'
            });
        });

        it('can update ARIA state on play', function() {
            state.el.trigger('play');
            expect($('.video_control.pause')).toHaveAttrs({
                'aria-disabled': 'false'
            });
        });

        it('can update ARIA state on video ends', function() {
            state.el.trigger('play');
            state.el.trigger('ended');
            expect($('.video_control.play')).toHaveAttrs({
                'aria-disabled': 'false'
            });
        });

        it('can update state on pause', function() {
            state.el.trigger('pause');
            expect(state.videoSaveStatePlugin.saveState).toHaveBeenCalledWith(true);
        });

        it('can start video playing on click', function() {
            $('.video_control.play').click();
            expect(state.videoCommands.execute).toHaveBeenCalledWith('togglePlayback');
        });

        it('can destroy itself', function() {
            state.videoPlayPauseControl.destroy();
            expect(state.videoPlayPauseControl).toBeUndefined();
        });
    });
}).call(this);
