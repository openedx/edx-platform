/* global YT */

// eslint-disable-next-line no-shadow-restricted-names
(function(require, define, undefined) {
    'use strict';

    require(
        ['video/03_video_player.js', 'hls', 'underscore'],
        function(VideoPlayer, HLS, _) {
            describe('VideoPlayer', function() {
                var STATUS = window.STATUS,
                    state,
                    oldOTBD,
                    emptyArguments;

                (function() {
                    emptyArguments = arguments;
                }());

                beforeEach(function() {
                    oldOTBD = window.onTouchBasedDevice;
                    // eslint-disable-next-line no-undef
                    window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                        .and.returnValue(null);
                });

                afterEach(function() {
                    $('source').remove();
                    window.onTouchBasedDevice = oldOTBD;
                    window.Video.previousState = null;
                    if (state.storage) {
                        state.storage.clear();
                    }
                    if (state.videoPlayer) {
                        _.result(state.videoPlayer, 'destroy');
                    }
                });

                describe('constructor', function() {
                    describe('always', function() {
                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer();
                            state.videoEl = $('video, iframe');
                        });

                        it('instanticate current time to zero', function() {
                            expect(state.videoPlayer.currentTime).toEqual(0);
                        });

                        it('set the element', function() {
                            expect(state.el).toHaveId('video_id');
                        });

                        it('create video control', function() {
                            expect(state.videoControl).toBeDefined();
                            expect(state.videoControl.el).toHaveClass('video-controls');
                        });

                        it('create video caption', function() {
                            expect(state.videoCaption).toBeDefined();
                            expect(state.speed).toEqual(1.5);
                            expect(state.config.transcriptTranslationUrl)
                                .toEqual('/transcript/translation/__lang__');
                        });

                        it('create video speed control', function() {
                            expect(state.videoSpeedControl).toBeDefined();
                            expect(state.videoSpeedControl.el).toHaveClass('speeds');
                            expect(state.speed).toEqual(1.5);
                        });

                        it('create video progress slider', function() {
                            expect(state.videoProgressSlider).toBeDefined();
                            expect(state.videoProgressSlider.el).toHaveClass('slider');
                        });

                        // All the toHandleWith() expect tests are not necessary for
                        // this version of Video. jQuery event system is not used to
                        // trigger and invoke methods. This is an artifact from
                        // previous version of Video.
                    });

                    it('create Youtube player', function() {
                        var events;

                        // eslint-disable-next-line no-undef
                        jasmine.stubRequests();
                        // eslint-disable-next-line no-undef
                        spyOn(window.YT, 'Player').and.callThrough();
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayerYouTube();
                        state.videoEl = $('video, iframe');

                        events = {
                            onReady: state.videoPlayer.onReady,
                            onStateChange: state.videoPlayer.onStateChange,
                            onPlaybackQualityChange: state.videoPlayer.onPlaybackQualityChange,
                            onError: state.videoPlayer.onError
                        };

                        expect(YT.Player).toHaveBeenCalledWith('id', {
                            playerVars: {
                                controls: 0,
                                wmode: 'transparent',
                                rel: 0,
                                showinfo: 0,
                                enablejsapi: 1,
                                modestbranding: 1,
                                html5: 1,
                                cc_load_policy: 0
                            },
                            videoId: 'cogebirgzzM',
                            events: events
                        });
                    });

                    it('create Flash player', function() {
                        var player;

                        // eslint-disable-next-line no-undef
                        spyOn($.fn, 'trigger');
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayerYouTube();
                        state.videoEl = state.el.find('video, iframe').width(100);
                        player = state.videoPlayer.player;
                        player.getAvailablePlaybackRates.and.returnValue([1]);
                        state.currentPlayerMode = 'html5';
                        // eslint-disable-next-line no-undef
                        spyOn(window.YT, 'Player').and.callThrough();
                        state.videoPlayer.onReady();

                        expect(YT.Player).toHaveBeenCalledWith('id', {
                            playerVars: {
                                controls: 0,
                                wmode: 'transparent',
                                rel: 0,
                                showinfo: 0,
                                enablejsapi: 1,
                                modestbranding: 1,
                                cc_load_policy: 0
                            },
                            videoId: 'abcdefghijkl',
                            // eslint-disable-next-line no-undef
                            events: jasmine.any(Object)
                        });

                        expect(state.resizer.setElement).toHaveBeenCalled();
                        expect(state.resizer.align).toHaveBeenCalled();
                    });

                    // We can't test the invocation of HTML5Video because it is not
                    // available globally. It is defined within the scope of Require
                    // JS.

                    describe('when on a touch based device', function() {
                        $.each(['iPad', 'Android'], function(index, device) {
                            it('create video volume control on' + device, function() {
                                window.onTouchBasedDevice.and.returnValue([device]);
                                // eslint-disable-next-line no-undef
                                state = jasmine.initializePlayer();

                                state.videoEl = $('video, iframe');

                                expect(state.el.find('.volume')).not.toExist();
                            });
                        });
                    });

                    describe('when not on a touch based device', function() {
                        // eslint-disable-next-line no-shadow
                        var oldOTBD;

                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer();

                            state.videoEl = $('video, iframe');
                        });

                        it('controls are in paused state', function() {
                            expect(state.videoPlayer.isPlaying()).toBe(false);
                        });
                    });
                });

                describe('onReady', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer();

                        state.videoEl = $('video, iframe');
                        // eslint-disable-next-line no-undef
                        spyOn(state.videoPlayer, 'play').and.callThrough();
                        state.videoPlayer.onReady();
                    });

                    it('autoplay the first video', function() {
                        expect(state.videoPlayer.play).not.toHaveBeenCalled();
                    });

                    it('invalid endTime is reset to null', function() {
                        expect(state.videoPlayer.endTime).toBe(null);
                    });
                });

                describe('onReady YouTube', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayerYouTube();

                        state.videoEl = $('video, iframe');
                    });

                    it('multiple speeds and flash mode, change back to html5 mode', function() {
                        var playbackRates = state.videoPlayer.player.getAvailablePlaybackRates();

                        state.currentPlayerMode = 'flash';
                        state.videoPlayer.onReady();
                        expect(playbackRates.length).toBe(4);
                        expect(state.currentPlayerMode).toBe('html5');
                    });
                });

                describe('onStateChange Youtube', function() {
                    describe('when the video is ended', function() {
                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayerYouTube();

                            state.videoEl = $('video, iframe');
                            // eslint-disable-next-line no-undef
                            spyOn($.fn, 'trigger').and.callThrough();
                            state.videoPlayer.onStateChange({
                                data: YT.PlayerState.ENDED
                            });
                        });

                        it('pause the video control', function() {
                            expect($('.video_control')).toHaveClass('play');
                        });

                        it('trigger pause and ended events', function() {
                            expect($.fn.trigger).toHaveBeenCalledWith('pause', emptyArguments);
                            expect($.fn.trigger).toHaveBeenCalledWith('ended', emptyArguments);
                        });
                    });
                });

                describe('onStateChange', function() {
                    describe('when the video is unstarted', function() {
                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer();
                            state.videoEl = $('video, iframe');
                            // eslint-disable-next-line no-undef
                            spyOn($.fn, 'trigger').and.callThrough();

                            state.videoPlayer.onStateChange({
                                data: YT.PlayerState.PAUSED
                            });
                        });

                        it('pause the video control', function() {
                            expect($('.video_control')).toHaveClass('play');
                        });

                        it('pause the video caption', function() {
                            expect($.fn.trigger).toHaveBeenCalledWith('pause', emptyArguments);
                        });
                    });

                    describe('when the video is playing', function() {
                        var oldState;

                        beforeEach(function() {
                            // Create the first instance of the player.
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer();
                            oldState = state;

                            // eslint-disable-next-line no-undef
                            spyOn(oldState.videoPlayer, 'onPause').and.callThrough();

                            // Now initialize a second instance.
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer();

                            state.videoEl = $('video, iframe');

                            // eslint-disable-next-line no-undef
                            spyOn(window, 'setInterval').and.returnValue(100);
                            // eslint-disable-next-line no-undef
                            spyOn($.fn, 'trigger').and.callThrough();

                            state.videoPlayer.onStateChange({
                                data: YT.PlayerState.PLAYING
                            });
                        });

                        it('set update interval', function() {
                            expect(window.setInterval).toHaveBeenCalledWith(
                                state.videoPlayer.update, 200
                            );
                            expect(state.videoPlayer.updateInterval).toEqual(100);
                        });

                        it('play the video control', function() {
                            expect($('.video_control')).toHaveClass('pause');
                        });

                        it('play the video caption', function() {
                            expect($.fn.trigger).toHaveBeenCalledWith('play', emptyArguments);
                        });
                    });

                    describe('when the video is paused', function() {
                        var currentUpdateIntrval;

                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer();

                            state.videoEl = $('video, iframe');

                            // eslint-disable-next-line no-undef
                            spyOn($.fn, 'trigger').and.callThrough();
                            state.videoPlayer.onStateChange({
                                data: YT.PlayerState.PLAYING
                            });

                            currentUpdateIntrval = state.videoPlayer.updateInterval;

                            state.videoPlayer.onStateChange({
                                data: YT.PlayerState.PAUSED
                            });
                        });

                        it('clear update interval', function() {
                            expect(state.videoPlayer.updateInterval).toBeUndefined();
                        });

                        it('pause the video control', function() {
                            expect($('.video_control')).toHaveClass('play');
                        });

                        it('pause the video caption', function() {
                            expect($.fn.trigger).toHaveBeenCalledWith('pause', emptyArguments);
                        });
                    });

                    describe('when the video is ended', function() {
                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer();

                            state.videoEl = $('video, iframe');
                            // eslint-disable-next-line no-undef
                            spyOn($.fn, 'trigger').and.callThrough();
                            state.videoPlayer.onStateChange({
                                data: YT.PlayerState.ENDED
                            });
                        });

                        it('pause the video control', function() {
                            expect($('.video_control')).toHaveClass('play');
                        });

                        it('pause the video caption', function() {
                            expect($.fn.trigger).toHaveBeenCalledWith('ended', emptyArguments);
                        });
                    });
                });

                describe('onSeek Youtube', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayerYouTube();
                        state.videoEl = $('video, iframe');
                    });

                    describe('when the video is playing', function() {
                        beforeEach(function() {
                            state.videoPlayer.onStateChange({
                                data: YT.PlayerState.PLAYING
                            });
                        });

                        it('Video has started playing', function() {
                            expect($('.video_control')).toHaveClass('pause');
                        });

                        it('seek the player', function() {
                            state.videoPlayer.seekTo(10);
                            expect(state.videoPlayer.currentTime).toBe(10);
                        });
                    });
                });

                describe('onSeek', function() {
                    beforeEach(function() {
                        // jasmine.Clock can't be used to fake out debounce with newer versions of underscore
                        // eslint-disable-next-line no-undef
                        spyOn(_, 'debounce').and.callFake(function(func) {
                            return function() {
                                func.apply(this, arguments);
                            };
                        });
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer();
                        state.videoEl = $('video, iframe');
                        // eslint-disable-next-line no-undef
                        spyOn(state.videoPlayer, 'duration').and.returnValue(120);
                    });

                    describe('when the video is playing', function() {
                        it('call runTimer in seekTo on player', function(done) {
                            state.videoPlayer.play();
                            // eslint-disable-next-line no-undef
                            jasmine.waitUntil(function() {
                                return state.videoPlayer.isPlaying();
                            }).then(function() {
                                // eslint-disable-next-line no-undef
                                spyOn(state.videoPlayer, 'stopTimer').and.callThrough();
                                // eslint-disable-next-line no-undef
                                spyOn(state.videoPlayer, 'runTimer').and.callThrough();
                                state.videoPlayer.seekTo(10);
                                expect(state.videoPlayer.currentTime).toBe(10);
                                expect(state.videoPlayer.stopTimer).toHaveBeenCalled();
                                expect(state.videoPlayer.runTimer).toHaveBeenCalled();
                            }).always(done);
                        });

                        it('seek the player', function() {
                            // eslint-disable-next-line no-undef
                            spyOn(state.videoPlayer.player, 'seekTo').and.callThrough();
                            state.videoProgressSlider.onSlide(
                                // eslint-disable-next-line no-undef
                                jQuery.Event('slide'), {value: 30}
                            );
                            expect(state.videoPlayer.currentTime).toBe(30);
                            expect(state.videoPlayer.player.seekTo).toHaveBeenCalledWith(30, true);
                        });

                        it('call updatePlayTime on player', function() {
                            // eslint-disable-next-line no-undef
                            spyOn(state.videoPlayer, 'updatePlayTime').and.callThrough();
                            state.videoProgressSlider.onSlide(
                                // eslint-disable-next-line no-undef
                                jQuery.Event('slide'), {value: 30}
                            );
                            expect(state.videoPlayer.currentTime).toBe(30);
                            expect(state.videoPlayer.updatePlayTime).toHaveBeenCalledWith(30, true);
                        });
                    });

                    it('when the player is not playing: set the current time', function() {
                        state.videoProgressSlider.onSlide(
                            // eslint-disable-next-line no-undef
                            jQuery.Event('slide'), {value: 20}
                        );
                        state.videoPlayer.pause();
                        expect(state.videoPlayer.currentTime).toBe(20);
                        state.videoProgressSlider.onSlide(
                            // eslint-disable-next-line no-undef
                            jQuery.Event('slide'), {value: 10}
                        );
                        expect(state.videoPlayer.currentTime).toBe(10);
                    });

                    describe('when the video is not playing', function() {
                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            spyOn(state.videoPlayer, 'setPlaybackRate')
                                .and.callThrough();
                        });

                        it('video has a correct speed', function() {
                            state.speed = '2.0';
                            state.videoPlayer.onPlay();
                            expect(state.videoPlayer.setPlaybackRate)
                                .toHaveBeenCalledWith('2.0');
                            state.videoPlayer.onPlay();
                            expect(state.videoPlayer.setPlaybackRate.calls.count())
                                .toEqual(1);
                        });
                    });
                });

                describe('onVolumeChange', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer();
                        state.videoPlayer.onReady();
                        state.videoEl = $('video, iframe');
                    });

                    it('set the volume on player', function() {
                        // eslint-disable-next-line no-undef
                        spyOn(state.videoPlayer.player, 'setVolume');
                        state.videoPlayer.onVolumeChange(60);
                        expect(state.videoPlayer.player.setVolume)
                            .toHaveBeenCalledWith(60);
                    });

                    describe('when the video is not playing', function() {
                        beforeEach(function() {
                            state.videoPlayer.player.setVolume('1');
                        });

                        it('video has a correct volume', function() {
                            // eslint-disable-next-line no-undef
                            spyOn(state.videoPlayer.player, 'setVolume');
                            state.videoVolumeControl.volume = 26;
                            state.el.trigger('play');
                            expect(state.videoPlayer.player.setVolume)
                                .toHaveBeenCalledWith(26);
                        });
                    });
                });

                describe('update', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer();

                        state.videoEl = $('video, iframe');

                        // eslint-disable-next-line no-undef
                        spyOn(state.videoPlayer, 'updatePlayTime').and.callThrough();
                    });

                    describe(
                        'when the current time is unavailable from the player',
                        function() {
                            beforeEach(function() {
                                state.videoPlayer.player.getCurrentTime = function() {
                                    return NaN;
                                };
                                state.videoPlayer.update();
                            });

                            it('does not trigger updatePlayTime event', function() {
                                expect(state.videoPlayer.updatePlayTime)
                                    .not.toHaveBeenCalled();
                            });
                        });

                    describe(
                        'when the current time is available from the player',
                        function() {
                            beforeEach(function() {
                                state.videoPlayer.player.getCurrentTime = function() {
                                    return 60;
                                };
                                state.videoPlayer.update();
                            });

                            it('trigger updatePlayTime event', function() {
                                expect(state.videoPlayer.updatePlayTime)
                                    .toHaveBeenCalledWith(60);
                            });
                        });
                });

                // Disabled 1/13/14 due to flakiness observed in master
                xdescribe('update with start & end time', function() {
                    var START_TIME = 1,
                        END_TIME = 2;

                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer(
                            {
                                start: START_TIME,
                                end: END_TIME
                            }
                        );

                        state.videoEl = $('video, iframe');

                        // eslint-disable-next-line no-undef
                        spyOn(state.videoPlayer, 'update').and.callThrough();
                        // eslint-disable-next-line no-undef
                        spyOn(state.videoPlayer, 'pause').and.callThrough();
                        // eslint-disable-next-line no-undef
                        spyOn(state.videoProgressSlider, 'notifyThroughHandleEnd')
                            .and.callThrough();
                    });

                    it(
                        'video is paused on first endTime, start & end time are reset',
                        function(done) {
                            var duration;

                            state.videoProgressSlider.notifyThroughHandleEnd.calls.reset();
                            state.videoPlayer.pause.calls.reset();
                            state.videoPlayer.play();

                            // eslint-disable-next-line no-undef
                            jasmine.waitUntil(function() {
                                duration = Math.round(state.videoPlayer.currentTime);
                                return state.videoPlayer.pause.calls.count() === 1;
                            }).then(function() {
                                expect(state.videoPlayer.startTime).toBe(0);
                                expect(state.videoPlayer.endTime).toBe(null);

                                expect(duration).toBe(END_TIME);

                                expect(state.videoProgressSlider.notifyThroughHandleEnd)
                                    .toHaveBeenCalledWith({end: true});
                            }).always(done);
                        });
                });

                describe('updatePlayTime', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayerYouTube();
                        state.videoEl = $('video, iframe');
                        // eslint-disable-next-line no-undef
                        spyOn(state.videoCaption, 'updatePlayTime').and.callThrough();
                        // eslint-disable-next-line no-undef
                        spyOn(state.videoProgressSlider, 'updatePlayTime').and.callThrough();
                    });

                    it('update the video playback time', function(done) {
                        var duration = 0;

                        // eslint-disable-next-line no-undef
                        jasmine.waitUntil(function() {
                            duration = state.videoPlayer.duration();

                            if (duration > 0) {
                                return true;
                            }

                            return false;
                        }).then(function() {
                            state.videoPlayer.goToStartTime = false;
                            state.videoPlayer.updatePlayTime(60);

                            expect($('.vidtime')).toHaveHtml('1:00 / 1:00');
                        }).always(done);
                    });

                    it('update the playback time on caption', function(done) {
                        // eslint-disable-next-line no-undef
                        jasmine.waitUntil(function() {
                            return state.videoPlayer.duration() > 0;
                        }, 1000).then(function() {
                            state.videoPlayer.goToStartTime = false;
                            state.videoPlayer.updatePlayTime(60);

                            expect(state.videoCaption.updatePlayTime)
                                .toHaveBeenCalledWith(60);
                        }).always(done);
                    });

                    it('update the playback time on progress slider', function(done) {
                        var duration = 0;

                        // eslint-disable-next-line no-undef
                        jasmine.waitUntil(function() {
                            duration = state.videoPlayer.duration();

                            return duration > 0;
                        }, 1000).then(function() {
                            state.videoPlayer.goToStartTime = false;
                            state.videoPlayer.updatePlayTime(60);

                            expect(state.videoProgressSlider.updatePlayTime)
                                .toHaveBeenCalledWith({
                                    time: 60,
                                    duration: duration
                                });
                        }).always(done);
                    });
                });

                // Disabled 1/13/14 due to flakiness observed in master
                xdescribe(
                    'updatePlayTime when start & end times are defined',
                    function() {
                        var START_TIME = 1,
                            END_TIME = 2;

                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer(
                                {
                                    start: START_TIME,
                                    end: END_TIME
                                }
                            );

                            state.videoEl = $('video, iframe');

                            // eslint-disable-next-line no-undef
                            spyOn(state.videoPlayer, 'updatePlayTime').and.callThrough();
                            // eslint-disable-next-line no-undef
                            spyOn(state.videoPlayer.player, 'seekTo').and.callThrough();
                            // eslint-disable-next-line no-undef
                            spyOn(state.videoProgressSlider, 'updateStartEndTimeRegion')
                                .and.callThrough();
                        });

                        it(
                            'when duration becomes available, updatePlayTime() is called',
                            function(done) {
                                var duration;

                                expect(state.videoPlayer.initialSeekToStartTime).toBeTruthy();
                                expect(state.videoPlayer.seekToStartTimeOldSpeed).toBe('void');

                                state.videoPlayer.play();

                                // eslint-disable-next-line no-undef
                                jasmine.waitUntil(function() {
                                    duration = state.videoPlayer.duration();

                                    return state.videoPlayer.isPlaying()
                        && state.videoPlayer.initialSeekToStartTime === false;
                                }).then(function() {
                                    expect(state.videoPlayer.startTime).toBe(START_TIME);
                                    expect(state.videoPlayer.endTime).toBe(END_TIME);

                                    expect(state.videoPlayer.player.seekTo)
                                        .toHaveBeenCalledWith(START_TIME);

                                    expect(state.videoProgressSlider.updateStartEndTimeRegion)
                                        .toHaveBeenCalledWith({duration: duration});

                                    expect(state.videoPlayer.seekToStartTimeOldSpeed)
                                        .toBe(state.speed);
                                }).always(done);
                            });
                    });

                describe('updatePlayTime with invalid endTime', function() {
                    beforeEach(function() {
                        state = {
                            el: $('#video_id'),
                            videoPlayer: {
                                duration: function() {
                                    // The video will be 60 seconds long.
                                    return 60;
                                },
                                goToStartTime: true,
                                startTime: undefined,
                                endTime: undefined,
                                player: {
                                    seekTo: function() {}
                                },
                                // eslint-disable-next-line no-undef
                                figureOutStartEndTime: jasmine.createSpy(),
                                // eslint-disable-next-line no-undef
                                figureOutStartingTime: jasmine.createSpy().and.returnValue(0)
                            },
                            config: {
                                savedVideoPosition: 0,
                                startTime: 0,

                                // We are setting the end-time to 10000 seconds. The
                                // video will be less than this, the code will reset
                                // the end time to `null` - i.e. to the end of the video.
                                // This is the expected behavior we will test for.
                                endTime: 10000
                            },
                            currentPlayerMode: 'html5',
                            trigger: function() {},
                            browserIsFirefox: false,
                            // eslint-disable-next-line no-undef
                            isFlashMode: jasmine.createSpy().and.returnValue(false)
                        };
                    });
                });

                describe('toggleFullScreen', function() {
                    describe('when the video player is not full screen', function() {
                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer();
                            // eslint-disable-next-line no-undef
                            jasmine.mockFullscreenAPI();
                            state.videoEl = $('video, iframe');
                            // eslint-disable-next-line no-undef
                            spyOn($.fn, 'trigger').and.callThrough();
                            $('.add-fullscreen').click();
                        });

                        it('add the video-fullscreen class', function() {
                            expect(state.el).toHaveClass('video-fullscreen');
                        });

                        it('tell VideoCaption to resize', function() {
                            expect($.fn.trigger).toHaveBeenCalledWith('fullscreen', [true]);
                            expect(state.resizer.setMode).toHaveBeenCalledWith('both');
                            expect(state.resizer.delta.substract).toHaveBeenCalled();
                        });
                    });

                    describe('when the video player already full screen', function() {
                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer();
                            // eslint-disable-next-line no-undef
                            jasmine.mockFullscreenAPI();
                            state.videoEl = $('video, iframe');
                            // eslint-disable-next-line no-undef
                            spyOn($.fn, 'trigger').and.callThrough();
                            state.videoFullScreen.enter();
                            $('.add-fullscreen').click();
                        });

                        it('remove the video-fullscreen class', function() {
                            expect(state.el).not.toHaveClass('video-fullscreen');
                        });

                        it('tell VideoCaption to resize', function() {
                            expect($.fn.trigger).toHaveBeenCalledWith('fullscreen', [false]);
                            expect(state.resizer.setMode)
                                .toHaveBeenCalledWith('width');
                            expect(state.resizer.delta.reset).toHaveBeenCalled();
                        });
                    });
                });

                describe('duration', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer();

                        state.videoEl = $('video, iframe');

                        // eslint-disable-next-line no-undef
                        spyOn(state.videoPlayer.player, 'getDuration').and.callThrough();
                        state.videoPlayer.duration();
                    });

                    it('delegate to the player', function() {
                        expect(state.videoPlayer.player.getDuration).toHaveBeenCalled();
                    });
                });

                describe('getDuration', function() {
                    beforeEach(function() {
                        // We need to make sure that metadata is returned via an AJAX
                        // request. Without the jasmine.stubRequests() below we will
                        // get the error:
                        //
                        //     this.metadata[this.youtubeId(...)] is undefined
                        // eslint-disable-next-line no-undef
                        jasmine.stubRequests();

                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayerYouTube();

                        state.videoEl = $('video, iframe');

                        // eslint-disable-next-line no-undef
                        spyOn(state, 'getDuration').and.callThrough();

                        // When `state.videoPlayer.player.getDuration()` returns a `0`,
                        // the fall-back function `state.getDuration()` will be called.
                        state.videoPlayer.player.getDuration.and.returnValue(0);
                    });

                    it('getDuration is called as a fall-back', function() {
                        state.videoPlayer.duration();

                        expect(state.getDuration).toHaveBeenCalled();
                    });
                });

                describe('volume', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer();

                        state.videoEl = $('video, iframe');

                        // eslint-disable-next-line no-undef
                        spyOn(state.videoPlayer.player, 'getVolume').and.callThrough();
                    });

                    it('set the player volume', function() {
                        var expectedValue = 60,
                            realValue;

                        state.videoPlayer.player.setVolume(60);
                        realValue = Math.round(state.videoPlayer.player.getVolume() * 100);

                        expect(realValue).toEqual(expectedValue);
                    });
                });

                describe('on Touch devices', function() {
                    it('`is-touch` class name is added to container', function() {
                        $.each(
                            ['iPad', 'Android', 'iPhone'],
                            function(index, device) {
                                window.onTouchBasedDevice.and.returnValue([device]);
                                // eslint-disable-next-line no-undef
                                state = jasmine.initializePlayer();

                                state.videoEl = $('video, iframe');

                                expect(state.el).toHaveClass('is-touch');
                            });
                    });

                    it('modules are not initialized on iPhone', function() {
                        window.onTouchBasedDevice.and.returnValue(['iPhone']);
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer();

                        state.videoEl = $('video, iframe');

                        var modules = [
                            state.videoControl, state.videoCaption, state.videoProgressSlider,
                            state.videoSpeedControl, state.videoVolumeControl
                        ];

                        $.each(modules, function(index, module) {
                            expect(module).toBeUndefined();
                        });
                    });

                    $.each(['iPad', 'Android'], function(index, device) {
                        var message = 'controls become visible after playing starts '
                    + 'on ' + device;

                        it(message, function(done) {
                            var controls;

                            window.onTouchBasedDevice.and.returnValue([device]);

                            // eslint-disable-next-line no-undef
                            state = jasmine.initializePlayer();
                            state.videoEl = $('video, iframe');
                            controls = state.el.find('.video-controls');

                            // eslint-disable-next-line no-undef
                            jasmine.waitUntil(function() {
                                return state.el.hasClass('is-initialized');
                            }).then(function() {
                                expect(controls).toHaveClass('is-hidden');
                                state.videoPlayer.play();
                                // eslint-disable-next-line no-undef
                                jasmine.waitUntil(function() {
                                    // Firefox does not return duration for videos until they have reached the end.
                                    // var duration = state.videoPlayer.duration();
                                    // return duration > 0 && state.videoPlayer.isPlaying();
                                    return state.videoPlayer.isPlaying();
                                }).then(function() {
                                    expect(controls).not.toHaveClass('is-hidden');
                                }).always(done);
                            });
                        });
                    });
                });

                describe('onSpeedChange', function() {
                    beforeEach(function() {
                        state = {
                            el: $(document),
                            speed: '1.50',
                            // eslint-disable-next-line no-undef
                            setSpeed: jasmine.createSpy(),
                            // eslint-disable-next-line no-undef
                            saveState: jasmine.createSpy(),
                            videoPlayer: {
                                currentTime: 60,
                                // eslint-disable-next-line no-undef
                                updatePlayTime: jasmine.createSpy(),
                                // eslint-disable-next-line no-undef
                                setPlaybackRate: jasmine.createSpy(),
                                // eslint-disable-next-line no-undef
                                player: jasmine.createSpyObj('player', ['setPlaybackRate'])
                            },
                            // eslint-disable-next-line no-undef
                            isFlashMode: jasmine.createSpy().and.returnValue(false)
                        };
                    });

                    describe('always', function() {
                        it('convert the current time to the new speed', function() {
                            state.isFlashMode.and.returnValue(true);
                            VideoPlayer.prototype.onSpeedChange.call(state, '0.75', false);
                            expect(state.videoPlayer.currentTime).toBe('120.000');
                        });

                        it('set video speed to the new speed', function() {
                            VideoPlayer.prototype.onSpeedChange.call(state, '0.75', false);
                            expect(state.setSpeed).toHaveBeenCalledWith(0.75);
                            expect(state.videoPlayer.setPlaybackRate)
                                .toHaveBeenCalledWith(0.75);
                        });
                    });
                });

                describe('setPlaybackRate', function() {
                    beforeEach(function() {
                        state = {
                            // eslint-disable-next-line no-undef
                            youtubeId: jasmine.createSpy().and.returnValue('videoId'),
                            // eslint-disable-next-line no-undef
                            isFlashMode: jasmine.createSpy().and.returnValue(false),
                            // eslint-disable-next-line no-undef
                            isHtml5Mode: jasmine.createSpy().and.returnValue(true),
                            // eslint-disable-next-line no-undef
                            isYoutubeType: jasmine.createSpy().and.returnValue(true),
                            // eslint-disable-next-line no-undef
                            setPlayerMode: jasmine.createSpy(),
                            // eslint-disable-next-line no-undef
                            trigger: jasmine.createSpy(),
                            videoPlayer: {
                                currentTime: 60,
                                // eslint-disable-next-line no-undef
                                isPlaying: jasmine.createSpy(),
                                // eslint-disable-next-line no-undef
                                seekTo: jasmine.createSpy(),
                                // eslint-disable-next-line no-undef
                                duration: jasmine.createSpy().and.returnValue(60),
                                // eslint-disable-next-line no-undef
                                updatePlayTime: jasmine.createSpy(),
                                // eslint-disable-next-line no-undef
                                setPlaybackRate: jasmine.createSpy(),
                                // eslint-disable-next-line no-undef
                                player: jasmine.createSpyObj('player', [
                                    'setPlaybackRate', 'loadVideoById', 'cueVideoById'
                                ])
                            }
                        };
                    });

                    it('in Flash mode and video is playing', function() {
                        state.isFlashMode.and.returnValue(true);
                        state.isHtml5Mode.and.returnValue(false);
                        state.videoPlayer.isPlaying.and.returnValue(true);
                        VideoPlayer.prototype.setPlaybackRate.call(state, '0.75');
                        expect(state.videoPlayer.player.setPlaybackRate)
                            .toHaveBeenCalledWith('0.75');
                    });

                    it('in Flash mode and video not started', function() {
                        state.isFlashMode.and.returnValue(true);
                        state.isHtml5Mode.and.returnValue(false);
                        state.videoPlayer.isPlaying.and.returnValue(false);
                        VideoPlayer.prototype.setPlaybackRate.call(state, '0.75');
                        expect(state.videoPlayer.player.setPlaybackRate).toHaveBeenCalledWith('0.75');
                    });

                    it('in HTML5 mode', function() {
                        state.isYoutubeType.and.returnValue(false);
                        VideoPlayer.prototype.setPlaybackRate.call(state, '0.75');
                        expect(state.videoPlayer.player.setPlaybackRate).toHaveBeenCalledWith('0.75');
                    });

                    it('Youtube video in FF, with new speed equal 1.0', function() {
                        state.browserIsFirefox = true;

                        state.videoPlayer.isPlaying.and.returnValue(false);
                        VideoPlayer.prototype.setPlaybackRate.call(state, '1.0');
                        expect(state.videoPlayer.player.setPlaybackRate).toHaveBeenCalledWith('1.0');
                    });
                });

                describe('HLS Video', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializeHLSPlayer();
                    });

                    it('does not show error message if hls is supported', function() {
                        expect($('.video-hls-error')).toHaveClass('is-hidden');
                    });

                    it('can extract hls video sources correctly', function() {
                        expect(state.HLSVideoSources).toEqual(['/base/fixtures/hls/hls.m3u8']);
                        expect(state.videoPlayer.player.hls).toBeDefined();
                    });

                    describe('on safari', function() {
                        beforeEach(function() {
                            // eslint-disable-next-line no-undef
                            spyOn(HLS, 'isSupported').and.returnValue(false);
                            // eslint-disable-next-line no-undef
                            state = jasmine.initializeHLSPlayer();
                            state.canPlayHLS = true;
                            state.browserIsSafari = true;
                        });

                        it('can use native hls playback support', function() {
                            expect(state.videoPlayer.player.hls).toBeUndefined();
                        });
                    });
                });

                describe('HLS Video Errors', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        spyOn(HLS, 'isSupported').and.returnValue(false);
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializeHLSPlayer({sources: ['/base/fixtures/hls/hls.m3u8']});
                    });

                    it('shows error message if hls is not supported', function() {
                        expect($('.video-hls-error')).not.toHaveClass('is-hidden');
                        expect($('.video-hls-error').text().trim()).toEqual(
                            'Your browser does not support this video format. Try using a different browser.'
                        );
                    });
                });

                describe('Video duration', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer();
                        // eslint-disable-next-line no-undef
                        spyOn(state.videoPlayer, 'duration').and.returnValue(61);
                    });

                    it('overrides the duration if not set', function(done) {
                        // eslint-disable-next-line no-undef
                        jasmine.waitUntil(function() {
                            return state.duration !== undefined;
                        }).then(function() {
                            expect(state.duration).toEqual(61);
                        }).always(done);
                    });
                });

                describe('Overlay Play Button', function() {
                    var playButtonOverlaySelector = '.video-wrapper .btn-play.fa.fa-youtube-play.fa-2x';
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer();
                    });

                    it('shows the play button after player is ready', function(done) {
                        // eslint-disable-next-line no-undef
                        jasmine.waitUntil(function() {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED;
                        }).then(function() {
                            expect($(playButtonOverlaySelector)).not.toHaveClass('is-hidden');
                        }).always(done);
                    });

                    it('hides the play button on play', function(done) {
                        $(state.videoPlayer.player.videoEl).trigger('click'); // play
                        // eslint-disable-next-line no-undef
                        jasmine.waitUntil(function() {
                            return state.videoPlayer.player.getPlayerState() === STATUS.PLAYING;
                        }).then(function() {
                            expect($(playButtonOverlaySelector)).toHaveClass('is-hidden');
                        }).always(done);
                    });

                    it('plays the video when overlay button is clicked', function() {
                        $('.video-wrapper .btn-play').trigger('click'); // play
                        expect(state.videoPlayer.player.getPlayerState()).toEqual(STATUS.PLAYING);
                        expect($(playButtonOverlaySelector)).toHaveClass('is-hidden');
                    });

                    it('shows the play button on pause', function(done) {
                        $(state.videoPlayer.player.videoEl).trigger('click'); // play
                        expect(state.videoPlayer.player.getPlayerState()).toEqual(STATUS.PLAYING);
                        $(state.videoPlayer.player.videoEl).trigger('click'); // pause
                        expect(state.videoPlayer.player.getPlayerState()).toEqual(STATUS.PAUSED);
                        // eslint-disable-next-line no-undef
                        jasmine.waitUntil(function() {
                            return $(playButtonOverlaySelector).attr('class').split(' ')
                                .indexOf('is-hidden') === -1;
                        }).then(function() {
                            expect($(playButtonOverlaySelector)).not.toHaveClass('is-hidden');
                        }).always(done);
                    });
                });

                describe('HLS Primary Playback', function() {
                    beforeEach(function() {
                        // eslint-disable-next-line no-undef
                        spyOn(window.YT, 'Player').and.callThrough();
                    });

                    afterEach(function() {
                        YT.Player.calls.reset();
                    });

                    it('loads youtube if flag is disabled', function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer('video_all.html', {
                            prioritizeHls: false,
                            streams: '0.5:7tqY6eQzVhE,1.0:cogebirgzzM,1.5:abcdefghijkl'
                        });
                        expect(state.config.prioritizeHls).toBeFalsy();
                        expect(YT.Player).toHaveBeenCalled();
                        expect(state.videoPlayer.player.hls).toBeUndefined();
                    });

                    it('does not load youtube if flag is enabled', function() {
                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer('video_all.html', {
                            prioritizeHls: true,
                            streams: '0.5:7tqY6eQzVhE,1.0:cogebirgzzM,1.5:abcdefghijkl',
                            sources: ['/base/fixtures/test.mp4', '/base/fixtures/test.webm', '/base/fixtures/hls/hls.m3u8']
                        });
                        expect(state.config.prioritizeHls).toBeTruthy();
                        expect(YT.Player).not.toHaveBeenCalled();
                        expect(state.videoPlayer.player.hls).toBeDefined();
                    });
                });
            });
        });
// eslint-disable-next-line no-undef
}(require, define));
