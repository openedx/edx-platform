(function () {
    describe('VideoPlayer Events', function () {
        var state, videoPlayer, player, videoControl, videoCaption,
            videoProgressSlider, videoSpeedControl, videoVolumeControl,
            oldOTBD, oldYT;

        function initialize(fixture, params) {
            if (_.isString(fixture)) {
                loadFixtures(fixture);
            } else {
                if (_.isObject(fixture)) {
                    params = fixture;
                }

                loadFixtures('video_all.html');
            }

            if (_.isObject(params)) {
                $('#example')
                    .find('#video_id')
                    .data(params);
            }

            state = new Video('#example');

            state.videoEl = $('video, iframe');
            videoPlayer = state.videoPlayer;
            player = videoPlayer.player;
            videoControl = state.videoControl;
            videoCaption = state.videoCaption;
            videoProgressSlider = state.videoProgressSlider;
            videoSpeedControl = state.videoSpeedControl;
            videoVolumeControl = state.videoVolumeControl;

            state.resizer = (function () {
                var methods = [
                        'align',
                        'alignByWidthOnly',
                        'alignByHeightOnly',
                        'setParams',
                        'setMode'
                    ],
                    obj = {};

                $.each(methods, function (index, method) {
                    obj[method] = jasmine.createSpy(method).andReturn(obj);
                });

                return obj;
            }());
        }

        function initializeYouTube() {
            initialize('video.html');
        }

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                .andReturn(null);
            oldYT = window.YT;

            jasmine.stubRequests();
            window.YT = {
              Player: function () {
                return {
                    getPlaybackQuality: function () {},
                    getDuration: function () { return 60; }
                };
              },
              PlayerState: oldYT.PlayerState,
              ready: function (callback) {
                  callback();
              }
            };
        });

        afterEach(function () {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
            window.YT = oldYT;
        });

        it('initialize', function(){
            runs(function () {
                initialize();
            });

            waitsFor(function () {
                return state.el.hasClass('is-initialized');
            }, 'Player is not initialized.', WAIT_TIMEOUT);

            runs(function () {
                expect('initialize').not.toHaveBeenTriggeredOn('.video');
            });
        });

        it('ready', function() {
            runs(function () {
                initialize();
            });

            waitsFor(function () {
                return state.el.hasClass('is-initialized');
            }, 'Player is not initialized.', WAIT_TIMEOUT);

            runs(function () {
                expect('ready').not.toHaveBeenTriggeredOn('.video');
            });
        });

        it('play', function() {
            initialize();
            videoPlayer.play();
            expect('play').not.toHaveBeenTriggeredOn('.video');
        });

        it('pause', function() {
            initialize();
            videoPlayer.play();
            videoPlayer.pause();
            expect('pause').not.toHaveBeenTriggeredOn('.video');
        });

        it('volumechange', function() {
            initialize();
            videoPlayer.onVolumeChange(60);

            expect('volumechange').not.toHaveBeenTriggeredOn('.video');
        });

        it('speedchange', function() {
            initialize();
            videoPlayer.onSpeedChange('2.0');

            expect('speedchange').not.toHaveBeenTriggeredOn('.video');
        });

        it('qualitychange', function() {
            initializeYouTube();
            videoPlayer.onPlaybackQualityChange();

            expect('qualitychange').not.toHaveBeenTriggeredOn('.video');
        });

        it('seek', function() {
            initialize();
            videoPlayer.onCaptionSeek({
                time: 1,
                type: 'any'
            });

            expect('seek').not.toHaveBeenTriggeredOn('.video');
        });

        it('ended', function() {
            initialize();
            videoPlayer.onEnded();

            expect('ended').not.toHaveBeenTriggeredOn('.video');
        });
    });
}).call(this);
