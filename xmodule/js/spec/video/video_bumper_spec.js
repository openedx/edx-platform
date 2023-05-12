// eslint-disable-next-line no-unused-vars
(function(WAIT_TIMEOUT) {
    'use strict';

    describe('VideoBumper', function() {
        var state, oldOTBD, waitForPlaying;

        // eslint-disable-next-line no-shadow
        waitForPlaying = function(state, done) {
            // eslint-disable-next-line no-undef
            jasmine.waitUntil(function() {
                return state.el.hasClass('is-playing');
            }).done(done);
        };

        beforeEach(function() {
            oldOTBD = window.onTouchBasedDevice;
            // eslint-disable-next-line no-undef
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').and.returnValue(null);
            // eslint-disable-next-line no-undef
            state = jasmine.initializePlayer('video_with_bumper.html');
            $('.poster .btn-play').click();
            // eslint-disable-next-line no-undef
            jasmine.clock().install();
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
            // eslint-disable-next-line no-undef
            jasmine.clock().uninstall();
        });

        it('can render the bumper video', function() {
            expect($('.is-bumper')).toExist();
        });

        it('can show the main video on error', function(done) {
            state.el.triggerHandler('error');
            // eslint-disable-next-line no-undef
            jasmine.clock().tick(20);
            expect($('.is-bumper')).not.toExist();
            waitForPlaying(state, done);
        });

        it('can show the main video once bumper ends', function(done) {
            state.el.trigger('ended');
            // eslint-disable-next-line no-undef
            jasmine.clock().tick(20);
            expect($('.is-bumper')).not.toExist();
            waitForPlaying(state, done);
        });

        it('can show the main video on skip', function(done) {
            state.bumperState.videoBumper.skip();
            // eslint-disable-next-line no-undef
            jasmine.clock().tick(20);
            expect($('.is-bumper')).not.toExist();
            waitForPlaying(state, done);
        });

        it('can stop the bumper video playing if it is too long', function(done) {
            state.el.trigger('timeupdate', [state.bumperState.videoBumper.maxBumperDuration + 1]);
            // eslint-disable-next-line no-undef
            jasmine.clock().tick(20);
            expect($('.is-bumper')).not.toExist();
            waitForPlaying(state, done);
        });

        it('can save appropriate states correctly on ended', function() {
            // eslint-disable-next-line no-undef
            var saveState = jasmine.createSpy('saveState');
            state.bumperState.videoSaveStatePlugin.saveState = saveState;
            state.el.trigger('ended');
            // eslint-disable-next-line no-undef
            jasmine.clock().tick(20);
            expect(saveState).toHaveBeenCalledWith(true, {bumper_last_view_date: true});
        });

        it('can save appropriate states correctly on skip', function() {
            // eslint-disable-next-line no-undef
            var saveState = jasmine.createSpy('saveState');
            state.bumperState.videoSaveStatePlugin.saveState = saveState;
            state.bumperState.videoBumper.skip();
            expect(state.storage.getItem('isBumperShown')).toBeTruthy();
            // eslint-disable-next-line no-undef
            jasmine.clock().tick(20);
            expect(saveState).toHaveBeenCalledWith(true, {bumper_last_view_date: true});
        });

        it('can save appropriate states correctly on error', function() {
            // eslint-disable-next-line no-undef
            var saveState = jasmine.createSpy('saveState');
            state.bumperState.videoSaveStatePlugin.saveState = saveState;
            state.el.triggerHandler('error');
            expect(state.storage.getItem('isBumperShown')).toBeTruthy();
            // eslint-disable-next-line no-undef
            jasmine.clock().tick(20);
            expect(saveState).toHaveBeenCalledWith(true, {bumper_last_view_date: true});
        });

        it('can save appropriate states correctly on skip and do not show again', function() {
            // eslint-disable-next-line no-undef
            var saveState = jasmine.createSpy('saveState');
            state.bumperState.videoSaveStatePlugin.saveState = saveState;
            state.bumperState.videoBumper.skipAndDoNotShowAgain();
            expect(state.storage.getItem('isBumperShown')).toBeTruthy();
            // eslint-disable-next-line no-undef
            jasmine.clock().tick(20);
            expect(saveState).toHaveBeenCalledWith(true, {bumper_last_view_date: true, bumper_do_not_show_again: true});
        });

        it('can destroy itself', function() {
            state.bumperState.videoBumper.destroy();
            expect(state.videoBumper).toBeUndefined();
        });
    });
}).call(this, window.WAIT_TIMEOUT);
