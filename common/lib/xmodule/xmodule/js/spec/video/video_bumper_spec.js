(function (WAIT_TIMEOUT) {
    'use strict';
    describe('VideoBumper', function () {
        var state, oldOTBD, waitForPlaying;

        waitForPlaying = function (state) {
            waitsFor(function () {
                return state.el.hasClass('is-playing');
            }, 'Player is not playing.', WAIT_TIMEOUT);
        };

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').andReturn(null);
            state = jasmine.initializePlayer('video_with_bumper.html');
            $('.poster .btn-play').click();
            jasmine.Clock.useMock();
        });

        afterEach(function () {
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

        it('can render the bumper video', function () {
            expect($('.is-bumper')).toExist();
        });

        it('can show the main video on error', function () {
            state.el.trigger('error');
            jasmine.Clock.tick(20);
            expect($('.is-bumper')).not.toExist();
            waitForPlaying(state);
        });

        it('can show the main video once bumper ends', function () {
            state.el.trigger('ended');
            jasmine.Clock.tick(20);
            expect($('.is-bumper')).not.toExist();
            waitForPlaying(state);
        });

        it('can show the main video on skip', function () {
            state.bumperState.videoBumper.skip();
            jasmine.Clock.tick(20);
            expect($('.is-bumper')).not.toExist();
            waitForPlaying(state);
        });

        it('can stop the bumper video playing if it is too long', function () {
            state.el.trigger('timeupdate', [state.bumperState.videoBumper.maxBumperDuration + 1]);
            jasmine.Clock.tick(20);
            expect($('.is-bumper')).not.toExist();
            waitForPlaying(state);
        });

        it('can save appropriate states correctly on ended', function () {
            var saveState = jasmine.createSpy('saveState');
            state.bumperState.videoSaveStatePlugin.saveState = saveState;
            state.el.trigger('ended');
            jasmine.Clock.tick(20);
            expect(saveState).toHaveBeenCalledWith(true, {
                bumper_last_view_date: true});
        });

        it('can save appropriate states correctly on skip', function () {
            var saveState = jasmine.createSpy('saveState');
            state.bumperState.videoSaveStatePlugin.saveState = saveState;
            state.bumperState.videoBumper.skip();
            expect(state.storage.getItem('isBumperShown')).toBeTruthy();
            jasmine.Clock.tick(20);
            expect(saveState).toHaveBeenCalledWith(true, {
                bumper_last_view_date: true});
        });

         it('can save appropriate states correctly on error', function () {
            var saveState = jasmine.createSpy('saveState');
            state.bumperState.videoSaveStatePlugin.saveState = saveState;
            state.el.trigger('error');
            expect(state.storage.getItem('isBumperShown')).toBeTruthy();
            jasmine.Clock.tick(20);
            expect(saveState).toHaveBeenCalledWith(true, {
                bumper_last_view_date: true});
        });

        it('can save appropriate states correctly on skip and do not show again', function () {
            var saveState = jasmine.createSpy('saveState');
            state.bumperState.videoSaveStatePlugin.saveState = saveState;
            state.bumperState.videoBumper.skipAndDoNotShowAgain();
            expect(state.storage.getItem('isBumperShown')).toBeTruthy();
            jasmine.Clock.tick(20);
            expect(saveState).toHaveBeenCalledWith(true, {
                bumper_last_view_date: true, bumper_do_not_show_again: true});
        });

        it('can destroy itself', function () {
            state.bumperState.videoBumper.destroy();
            expect(state.videoBumper).toBeUndefined();
        });
    });
}).call(this, window.WAIT_TIMEOUT);
