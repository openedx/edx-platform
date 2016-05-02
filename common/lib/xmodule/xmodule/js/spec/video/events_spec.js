(function (undefined) {
    describe('VideoPlayer Events', function () {
        var state, oldOTBD;

        describe('HTML5', function () {
            beforeEach(function () {
                oldOTBD = window.onTouchBasedDevice;
                window.onTouchBasedDevice = jasmine
                    .createSpy('onTouchBasedDevice')
                    .andReturn(null);

                jasmine.stubRequests();

                state = jasmine.initializePlayer();

                state.videoEl = $('video, iframe');
            });

            afterEach(function () {
                $('source').remove();
                window.onTouchBasedDevice = oldOTBD;
                state.storage.clear();
            });

            it('initialize', function () {
                waitsFor(function () {
                    return state.el.hasClass('is-initialized');
                }, 'Player is not initialized.', WAIT_TIMEOUT);

                runs(function () {
                    expect('initialize').not.toHaveBeenTriggeredOn('.video');
                });
            });

            it('ready', function () {
                waitsFor(function () {
                    return state.el.hasClass('is-initialized');
                }, 'Player is not initialized.', WAIT_TIMEOUT);

                runs(function () {
                    expect('ready').not.toHaveBeenTriggeredOn('.video');
                });
            });

            it('play', function () {
                state.videoPlayer.play();
                expect('play').not.toHaveBeenTriggeredOn('.video');
            });

            it('pause', function () {
                state.videoPlayer.play();
                state.videoPlayer.pause();
                expect('pause').not.toHaveBeenTriggeredOn('.video');
            });

            it('volumechange', function () {
                state.videoPlayer.onVolumeChange(60);

                expect('volumechange').not.toHaveBeenTriggeredOn('.video');
            });

            it('speedchange', function () {
                state.videoPlayer.onSpeedChange('2.0');

                expect('speedchange').not.toHaveBeenTriggeredOn('.video');
            });

            it('seek', function () {
                state.videoPlayer.onCaptionSeek({
                    time: 1,
                    type: 'any'
                });

                expect('seek').not.toHaveBeenTriggeredOn('.video');
            });

            it('ended', function () {
                state.videoPlayer.onEnded();

                expect('ended').not.toHaveBeenTriggeredOn('.video');
            });
        });

        describe('YouTube', function () {
            beforeEach(function () {
                oldOTBD = window.onTouchBasedDevice;
                window.onTouchBasedDevice = jasmine
                    .createSpy('onTouchBasedDevice')
                    .andReturn(null);

                jasmine.stubRequests();

                state = jasmine.initializePlayerYouTube();
            });

            afterEach(function () {
                $('source').remove();
                window.onTouchBasedDevice = oldOTBD;
            });

            it('qualitychange', function () {
                state.videoPlayer.onPlaybackQualityChange();

                expect('qualitychange').not.toHaveBeenTriggeredOn('.video');
            });
        });
    });

}).call(this);
