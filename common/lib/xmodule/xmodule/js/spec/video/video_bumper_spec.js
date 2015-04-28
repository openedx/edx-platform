(function (WAIT_TIMEOUT) {
    'use strict';

    describe('VideoBumper', function () {
        var state, oldOTBD, saveState;

        describe('VideoWithBumper', function () {

            beforeEach(function () {
                oldOTBD = window.onTouchBasedDevice;
                window.onTouchBasedDevice = jasmine
                    .createSpy('onTouchBasedDevice').andReturn(null);

    // Start the player with video bumper
                state = jasmine.initializePlayer('video_with_bumper.html');
                spyOn(state.bumperState.videoCommands, 'execute');
                saveState = jasmine.createSpy('saveState');
                state.bumperState.videoSaveStatePlugin.saveState = saveState;
            });

            afterEach(function () {
                $('source').remove();
                state.storage.clear();
                window.Video.previousState = null;
                window.onTouchBasedDevice = oldOTBD;
            });

            it('can render the poster', function () {
                expect($('.poster')).toExist();
            });

            it('can render the bumper video', function () {
                expect($('.is-bumper')).toExist();
            });

            it('can start bumper playing on click', function () {
                $('.poster .btn-play').click();
                expect(state.bumperState.videoCommands.execute).toHaveBeenCalledWith('play');
            });

            it('can show the main video on error', function () {
                state.bumperState.el.trigger('error');
                expect($('.is-bumper')).not.toExist();

                waitsFor(function () {
                    return state.el.hasClass('is-playing');
                }, 'Player is not plaing.', WAIT_TIMEOUT);
            });

            it('can show the main video once bumper ends', function () {
                //state.bumperState.videoPlayer.onEnded();
                state.bumperState.el.trigger('ended');
                expect($('.is-bumper')).not.toExist();


                waitsFor(function () {
                    return state.el.hasClass('is-initialized');
                }, 'Player is not initialized.', WAIT_TIMEOUT);

                //waitsFor(function () {
                //    return expect($('.video-controls')).toExist();
                //}, 'Player is not plaing.', WAIT_TIMEOUT);

                waitsFor(function () {
                    return state.el.hasClass('is-playing');
                }, 'Player is not plaing.', WAIT_TIMEOUT);

            });

            it('can show the main video on skip', function () {
                state.bumperState.el.trigger('skip');
                expect($('.is-bumper')).not.toExist();

                waitsFor(function () {
                    return state.el.hasClass('is-playing');
                }, 'Player is not plaing.', WAIT_TIMEOUT);
            });

            it('can stop the bumper video playing if it is too long', function () {
                state.bumperState.el.trigger('timeupdate', [state.bumperState.videoBumper.maxBumperDuration + 1]);
                expect($('.is-bumper')).not.toExist();

                waitsFor(function () {
                    return state.el.hasClass('is-playing');
                }, 'Player is not plaing.', WAIT_TIMEOUT);
            });

            it('can save appropriate states correctly on ended', function () {
                state.bumperState.el.trigger('ended');
                expect(state.bumperState.storage.getItem('isBumperShown')).toBe(true);
                expect(saveState).toHaveBeenCalledWith(true, {date_last_view_bumper: true});
            });

            it('can save appropriate states correctly on skip', function () {
                state.bumperState.el.trigger('skip');
                expect(state.bumperState.storage.getItem('isBumperShown')).toBe(true);
                expect(saveState).toHaveBeenCalledWith(true, {date_last_view_bumper: true});
            });

             it('can save appropriate states correctly on error', function () {
                 state.bumperState.el.trigger('error');
                 expect(state.bumperState.storage.getItem('isBumperShown')).toBe(true);
                 expect(saveState).toHaveBeenCalledWith(true, {date_last_view_bumper: true});
            });

            it('can save appropriate states correctly on skip and do not show again', function () {
                state.bumperState.videoBumper.skipAndDoNotShowAgain();
                expect(state.bumperState.storage.getItem('isBumperShown')).toBe(true);
                expect(saveState).toHaveBeenCalledWith(true, {date_last_view_bumper: true, do_not_show_again_bumper: true});
            });

            it('can destroy itself', function () {
                state.bumperState.videoBumper.destroy();
                expect(state.bumperState.videoBumper).toBeUndefined();
            });

        });


        describe('VideoWithoutBumper', function () {

            beforeEach(function () {
                oldOTBD = window.onTouchBasedDevice;
                window.onTouchBasedDevice = jasmine
                    .createSpy('onTouchBasedDevice').andReturn(null);

                state = jasmine.initializePlayer('video.html');
            });

            afterEach(function () {
                $('source').remove();
                state.storage.clear();
                window.Video.previousState = null;
                window.onTouchBasedDevice = oldOTBD;
            });

            it('do not initialize the bumper if it is disabled', function () {
                expect($('.is-bumper')).not.toExist();
                expect(state.bumperState).toBeUndefined()
            });
        });



    });
}).call(this, window.WAIT_TIMEOUT);
