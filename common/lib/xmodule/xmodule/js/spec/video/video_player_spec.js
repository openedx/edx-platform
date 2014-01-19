(function () {
    describe('VideoPlayer', function () {
        var state, videoPlayer, player, videoControl, videoCaption,
            videoProgressSlider, videoSpeedControl, videoVolumeControl,
            oldOTBD;

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
        });

        afterEach(function () {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function () {
            describe('always', function () {
                beforeEach(function () {
                    initialize();
                });

                it('instanticate current time to zero', function () {
                    expect(videoPlayer.currentTime).toEqual(0);
                });

                it('set the element', function () {
                    expect(state.el).toHaveId('video_id');
                });

                it('create video control', function () {
                    expect(videoControl).toBeDefined();
                    expect(videoControl.el).toHaveClass('video-controls');
                });

                it('create video caption', function () {
                    expect(videoCaption).toBeDefined();
                    expect(state.youtubeId()).toEqual('Z5KLxerq05Y');
                    expect(state.speed).toEqual('1.0');
                    expect(state.config.caption_asset_path)
                        .toEqual('/static/subs/');
                });

                it('create video speed control', function () {
                    expect(videoSpeedControl).toBeDefined();
                    expect(videoSpeedControl.el).toHaveClass('speeds');
                    expect(videoSpeedControl.speeds)
                        .toEqual([ '0.75', '1.0', '1.25', '1.50' ]);
                    expect(state.speed).toEqual('1.0');
                });

                it('create video progress slider', function () {
                    expect(videoProgressSlider).toBeDefined();
                    expect(videoProgressSlider.el).toHaveClass('slider');
                });

                // All the toHandleWith() expect tests are not necessary for
                // this version of Video. jQuery event system is not used to
                // trigger and invoke methods. This is an artifact from
                // previous version of Video.
            });

            it('create Youtube player', function () {
                var oldYT = window.YT, events;

                jasmine.stubRequests();

                window.YT = {
                    Player: function () { },
                    PlayerState: oldYT.PlayerState,
                    ready: function (callback) {
                        callback();
                    }
                };

                spyOn(window.YT, 'Player');

                initializeYouTube();

                events = {
                    onReady:                 videoPlayer.onReady,
                    onStateChange:           videoPlayer.onStateChange,
                    onPlaybackQualityChange: videoPlayer
                        .onPlaybackQualityChange
                };

                expect(YT.Player).toHaveBeenCalledWith('id', {
                    playerVars: {
                        controls: 0,
                        wmode: 'transparent',
                        rel: 0,
                        showinfo: 0,
                        enablejsapi: 1,
                        modestbranding: 1,
                        html5: 1
                    },
                    videoId: 'cogebirgzzM',
                    events: events
                });

                window.YT = oldYT;
            });

            // We can't test the invocation of HTML5Video because it is not
            // available globally. It is defined within the scope of Require
            // JS.

            describe('when on a touch based device', function () {
                $.each(['iPad', 'Android'], function(index, device) {
                    it('create video volume control on' + device, function() {
                        window.onTouchBasedDevice.andReturn([device]);
                        initialize();
                        expect(videoVolumeControl).toBeUndefined();
                        expect(state.el.find('div.volume')).not.toExist();
                    });
                });
            });

            describe('when not on a touch based device', function () {
                var oldOTBD;

                beforeEach(function () {
                    initialize();
                });

                it('controls are in paused state', function () {
                    expect(videoControl.isPlaying).toBe(false);
                });
            });
        });

        describe('onReady', function () {
            beforeEach(function () {
                initialize();

                spyOn(videoPlayer, 'log').andCallThrough();
                spyOn(videoPlayer, 'play').andCallThrough();
                videoPlayer.onReady();
            });

            it('log the load_video event', function () {
                expect(videoPlayer.log).toHaveBeenCalledWith('load_video');
            });

            it('autoplay the first video', function () {
                expect(videoPlayer.play).not.toHaveBeenCalled();
            });
        });

        describe('onStateChange', function () {
            describe('when the video is unstarted', function () {
                beforeEach(function () {
                    initialize();

                    spyOn(videoControl, 'pause').andCallThrough();
                    spyOn(videoCaption, 'pause').andCallThrough();

                    videoPlayer.onStateChange({
                    data: YT.PlayerState.PAUSED
                    });
                });

                it('pause the video control', function () {
                    expect(videoControl.pause).toHaveBeenCalled();
                });

                it('pause the video caption', function () {
                    expect(videoCaption.pause).toHaveBeenCalled();
                });
            });

            describe('when the video is playing', function () {
                var oldState;

                beforeEach(function () {
                    // Create the first instance of the player.
                    initialize();
                    oldState = state;

                    spyOn(oldState.videoPlayer, 'onPause').andCallThrough();

                    // Now initialize a second instance.
                    initialize();

                    spyOn(videoPlayer, 'log').andCallThrough();
                    spyOn(window, 'setInterval').andReturn(100);
                    spyOn(videoControl, 'play');
                    spyOn(videoCaption, 'play');

                    videoPlayer.onStateChange({
                        data: YT.PlayerState.PLAYING
                    });
                });

                it('log the play_video event', function () {
                    expect(videoPlayer.log).toHaveBeenCalledWith(
                        'play_video', { currentTime: 0 }
                    );
                });

                it('pause other video player', function () {
                    expect(oldState.videoPlayer.onPause).toHaveBeenCalled();
                });

                it('set update interval', function () {
                    expect(window.setInterval).toHaveBeenCalledWith(
                        videoPlayer.update, 200
                    );
                    expect(videoPlayer.updateInterval).toEqual(100);
                });

                it('play the video control', function () {
                    expect(videoControl.play).toHaveBeenCalled();
                });

                it('play the video caption', function () {
                    expect(videoCaption.play).toHaveBeenCalled();
                });
            });

            describe('when the video is paused', function () {
                var currentUpdateIntrval;

                beforeEach(function () {
                    initialize();

                    spyOn(videoPlayer, 'log').andCallThrough();
                    spyOn(videoControl, 'pause').andCallThrough();
                    spyOn(videoCaption, 'pause').andCallThrough();

                    videoPlayer.onStateChange({
                        data: YT.PlayerState.PLAYING
                    });

                    currentUpdateIntrval = videoPlayer.updateInterval;

                    videoPlayer.onStateChange({
                        data: YT.PlayerState.PAUSED
                    });
                });

                it('log the pause_video event', function () {
                    expect(videoPlayer.log).toHaveBeenCalledWith(
                        'pause_video', { currentTime: 0 }
                    );
                });

                it('clear update interval', function () {
                    expect(videoPlayer.updateInterval).toBeUndefined();
                });

                it('pause the video control', function () {
                    expect(videoControl.pause).toHaveBeenCalled();
                });

                it('pause the video caption', function () {
                    expect(videoCaption.pause).toHaveBeenCalled();
                });
            });

            describe('when the video is ended', function () {
                beforeEach(function () {
                    initialize();

                    spyOn(videoControl, 'pause').andCallThrough();
                    spyOn(videoCaption, 'pause').andCallThrough();

                    videoPlayer.onStateChange({
                        data: YT.PlayerState.ENDED
                    });
                });

                it('pause the video control', function () {
                    expect(videoControl.pause).toHaveBeenCalled();
                });

                it('pause the video caption', function () {
                    expect(videoCaption.pause).toHaveBeenCalled();
                });
            });
        });

        describe('onSeek', function () {
            beforeEach(function () {
                initialize();

                runs(function () {
                    state.videoPlayer.play();
                });

                waitsFor(function () {
                    duration = videoPlayer.duration();

                    return duration > 0 && videoPlayer.isPlaying();
                }, 'video begins playing', WAIT_TIMEOUT);
            });

            it('Slider event causes log update', function () {

                runs(function () {
                    var currentTime = videoPlayer.currentTime;

                    spyOn(videoPlayer, 'log');
                    videoProgressSlider.onSlide(
                        jQuery.Event('slide'), { value: 2 }
                    );

                    expect(videoPlayer.log).toHaveBeenCalledWith(
                        'seek_video',
                        {
                            old_time: currentTime,
                            new_time: 2,
                            type: 'onSlideSeek'
                        }
                    );
                });
            });

            it('seek the player', function () {
                runs(function () {
                    spyOn(videoPlayer.player, 'seekTo');
                    videoProgressSlider.onSlide(
                        jQuery.Event('slide'), { value: 60 }
                    );

                    expect(videoPlayer.player.seekTo)
                        .toHaveBeenCalledWith(60, true);
                });
            });

            it('call updatePlayTime on player', function () {
                runs(function () {
                    spyOn(videoPlayer, 'updatePlayTime');
                    videoProgressSlider.onSlide(
                        jQuery.Event('slide'), { value: 60 }
                    );

                    expect(videoPlayer.updatePlayTime)
                        .toHaveBeenCalledWith(60);
                });
            });

            // Disabled 10/25/13 due to flakiness in master
            xit(
                'when the player is not playing: set the current time',
                function ()
            {
                runs(function () {
                    videoProgressSlider.onSlide(
                        jQuery.Event('slide'), { value: 20 }
                    );
                    videoPlayer.pause();
                    videoProgressSlider.onSlide(
                        jQuery.Event('slide'), { value: 10 }
                    );

                    waitsFor(function () {
                        return Math.round(videoPlayer.currentTime) === 10;
                    }, 'currentTime got updated', 10000);
                });
            });
        });

        describe('onSpeedChange', function () {
            beforeEach(function () {
                initialize();

                spyOn(videoPlayer, 'updatePlayTime').andCallThrough();
                spyOn(state, 'setSpeed').andCallThrough();
                spyOn(videoPlayer, 'log').andCallThrough();
                spyOn(videoPlayer.player, 'setPlaybackRate').andCallThrough();
            });

            describe('always', function () {
                beforeEach(function () {

                    videoPlayer.currentTime = 60;
                    videoPlayer.onSpeedChange('0.75', false);
                });

                it('check if speed_change_video is logged', function () {
                    expect(videoPlayer.log).toHaveBeenCalledWith(
                        'speed_change_video',
                        {
                            current_time: videoPlayer.currentTime,
                            old_speed: '1.0',
                            new_speed: '0.75'
                        }
                    );
                });

                it('convert the current time to the new speed', function () {
                    expect(videoPlayer.currentTime).toEqual(60);
                });

                it('set video speed to the new speed', function () {
                    expect(state.setSpeed).toHaveBeenCalledWith('0.75', false);
                });
            });

            describe('when the video is playing', function () {
                beforeEach(function () {
                    videoPlayer.currentTime = 60;
                    videoPlayer.play();
                    videoPlayer.onSpeedChange('0.75', false);
                });

                it('trigger updatePlayTime event', function () {
                    expect(videoPlayer.player.setPlaybackRate)
                        .toHaveBeenCalledWith('0.75');
                });
            });

            describe('when the video is not playing', function () {
                beforeEach(function () {
                    videoPlayer.onSpeedChange('0.75', false);
                });

                it('trigger updatePlayTime event', function () {
                    expect(videoPlayer.player.setPlaybackRate)
                        .toHaveBeenCalledWith('0.75');
                });

                it('video has a correct speed', function () {
                    spyOn(videoPlayer, 'onSpeedChange');
                    state.speed = '2.0';
                    videoPlayer.onPlay();
                    expect(videoPlayer.onSpeedChange).toHaveBeenCalledWith('2.0');
                    videoPlayer.onPlay();
                    expect(videoPlayer.onSpeedChange.calls.length).toEqual(1);
                });

                it('video has a correct volume', function () {
                    spyOn(videoPlayer.player, 'setVolume');
                    state.currentVolume = '0.26';
                    videoPlayer.onPlay();
                    expect(videoPlayer.player.setVolume).toHaveBeenCalledWith('0.26');
                });
            });
        });

        describe('onVolumeChange', function () {
            beforeEach(function () {
                initialize();
            });

            it('set the volume on player', function () {
                spyOn(videoPlayer.player, 'setVolume');
                videoPlayer.onVolumeChange(60);
                expect(videoPlayer.player.setVolume).toHaveBeenCalledWith(60);
            });

            describe('when the video is not playing', function () {
                beforeEach(function () {
                    videoPlayer.player.setVolume('1');
                });

                it('video has a correct volume', function () {
                    spyOn(videoPlayer.player, 'setVolume');
                    state.currentVolume = '0.26';
                    videoPlayer.onPlay();
                    expect(videoPlayer.player.setVolume).toHaveBeenCalledWith('0.26');
                });
            });
        });

        describe('update', function () {
            beforeEach(function () {
                initialize();

                spyOn(videoPlayer, 'updatePlayTime').andCallThrough();
            });

            describe(
                'when the current time is unavailable from the player',
                function ()
            {
                beforeEach(function () {
                    videoPlayer.player.getCurrentTime = function () {
                        return NaN;
                    };
                    videoPlayer.update();
                });

                it('does not trigger updatePlayTime event', function () {
                    expect(videoPlayer.updatePlayTime).not.toHaveBeenCalled();
                });
            });

            describe(
                'when the current time is available from the player',
                function ()
            {
                beforeEach(function () {
                    videoPlayer.player.getCurrentTime = function () {
                        return 60;
                    };
                    videoPlayer.update();
                });

                it('trigger updatePlayTime event', function () {
                    expect(videoPlayer.updatePlayTime)
                        .toHaveBeenCalledWith(60);
                });
            });
        });

        describe('update with start & end time', function () {
            var START_TIME = 1, END_TIME = 2;

            beforeEach(function () {
                initialize({start: START_TIME, end: END_TIME});

                spyOn(videoPlayer, 'update').andCallThrough();
                spyOn(videoPlayer, 'pause').andCallThrough();
                spyOn(videoProgressSlider, 'notifyThroughHandleEnd')
                    .andCallThrough();
            });

            it('video is paused on first endTime, start & end time are reset', function () {
                var duration;

                videoProgressSlider.notifyThroughHandleEnd.reset();
                videoPlayer.pause.reset();
                videoPlayer.play();

                waitsFor(function () {
                    duration = Math.round(videoPlayer.currentTime);

                    return videoPlayer.pause.calls.length === 1;
                }, 'pause() has been called', WAIT_TIMEOUT);

                runs(function () {
                    expect(videoPlayer.startTime).toBe(0);
                    expect(videoPlayer.endTime).toBe(null);

                    expect(duration).toBe(END_TIME);

                    expect(videoProgressSlider.notifyThroughHandleEnd)
                        .toHaveBeenCalledWith({end: true});
                });
            });
        });

        describe('updatePlayTime', function () {
            beforeEach(function () {
                initialize();

                spyOn(videoCaption, 'updatePlayTime').andCallThrough();
                spyOn(videoProgressSlider, 'updatePlayTime').andCallThrough();
            });

            it('update the video playback time', function () {
                var duration = 0;

                waitsFor(function () {
                    duration = videoPlayer.duration();

                    if (duration > 0) {
                        return true;
                    }

                    return false;
                }, 'Video is fully loaded.', WAIT_TIMEOUT);

                runs(function () {
                    var htmlStr;

                    videoPlayer.updatePlayTime(60);

                    htmlStr = $('.vidtime').html();

                    // We resort to this trickery because Firefox and Chrome
                    // round the total time a bit differently.
                    if (
                        htmlStr.match('1:00 / 1:01') ||
                        htmlStr.match('1:00 / 1:00')
                    ) {
                        expect(true).toBe(true);
                    } else {
                        expect(true).toBe(false);
                    }

                    // The below test has been replaced by above trickery:
                    //
                    //     expect($('.vidtime')).toHaveHtml('1:00 / 1:01');
                });
            });

            it('update the playback time on caption', function () {
                waitsFor(function () {
                    return videoPlayer.duration() > 0;
                }, 'Video is fully loaded.', WAIT_TIMEOUT);

                runs(function () {
                    videoPlayer.updatePlayTime(60);

                    expect(videoCaption.updatePlayTime)
                        .toHaveBeenCalledWith(60);
                });
            });

            it('update the playback time on progress slider', function () {
                var duration = 0;

                waitsFor(function () {
                    duration = videoPlayer.duration();

                    return duration > 0;
                }, 'Video is fully loaded.', WAIT_TIMEOUT);

                runs(function () {
                    videoPlayer.updatePlayTime(60);

                    expect(videoProgressSlider.updatePlayTime)
                        .toHaveBeenCalledWith({
                            time: 60,
                            duration: duration
                        });
                });
            });
        });

        describe('updatePlayTime when start & end times are defined', function () {
            var START_TIME = 1,
                END_TIME = 2;

            beforeEach(function () {
                initialize({start: START_TIME, end: END_TIME});

                spyOn(videoPlayer, 'updatePlayTime').andCallThrough();
                spyOn(videoPlayer.player, 'seekTo').andCallThrough();
                spyOn(videoProgressSlider, 'updateStartEndTimeRegion')
                    .andCallThrough();
            });

            it('when duration becomes available, updatePlayTime() is called', function () {
                var duration;

                expect(videoPlayer.initialSeekToStartTime).toBeTruthy();
                expect(videoPlayer.seekToStartTimeOldSpeed).toBe('void');

                videoPlayer.play();

                waitsFor(function () {
                    duration = videoPlayer.duration();

                    return videoPlayer.isPlaying() &&
                        videoPlayer.initialSeekToStartTime === false;
                }, 'duration becomes available', WAIT_TIMEOUT);

                runs(function () {
                    expect(videoPlayer.startTime).toBe(START_TIME);
                    expect(videoPlayer.endTime).toBe(END_TIME);

                    expect(videoPlayer.player.seekTo).toHaveBeenCalledWith(START_TIME);

                    expect(videoProgressSlider.updateStartEndTimeRegion)
                        .toHaveBeenCalledWith({duration: duration});

                    expect(videoPlayer.seekToStartTimeOldSpeed).toBe(state.speed);
                });
            });
        });

        describe('updatePlayTime with invalid endTime', function () {
            beforeEach(function () {
                initialize({end: 100000});

                spyOn(videoPlayer, 'updatePlayTime').andCallThrough();
            });

            it('invalid endTime is reset to null', function () {
                var duration;

                videoPlayer.updatePlayTime.reset();
                videoPlayer.play();

                waitsFor(function () {
                    return videoPlayer.isPlaying() &&
                        videoPlayer.initialSeekToStartTime === false;
                }, 'updatePlayTime was invoked and duration is set', WAIT_TIMEOUT);

                runs(function () {
                    expect(videoPlayer.endTime).toBe(null);
                });
            });
        });

        describe('toggleFullScreen', function () {
            describe('when the video player is not full screen', function () {
                beforeEach(function () {
                    initialize();
                    spyOn(videoCaption, 'resize').andCallThrough();
                    videoControl.toggleFullScreen(jQuery.Event('click'));
                });

                it('replace the full screen button tooltip', function () {
                    expect($('.add-fullscreen'))
                        .toHaveAttr('title', 'Exit full browser');
                });

                it('add the video-fullscreen class', function () {
                    expect(state.el).toHaveClass('video-fullscreen');
                });

                it('tell VideoCaption to resize', function () {
                    expect(videoCaption.resize).toHaveBeenCalled();
                    expect(state.resizer.setMode).toHaveBeenCalled();
                });
            });

            describe('when the video player already full screen', function () {
                beforeEach(function () {
                    initialize();
                    spyOn(videoCaption, 'resize').andCallThrough();

                    state.el.addClass('video-fullscreen');
                    videoControl.fullScreenState = true;
                    isFullScreen = true;
                    videoControl.fullScreenEl.attr('title', 'Exit-fullscreen');

                    videoControl.toggleFullScreen(jQuery.Event('click'));
                });

                it('replace the full screen button tooltip', function () {
                    expect($('.add-fullscreen'))
                        .toHaveAttr('title', 'Fill browser');
                });

                it('remove the video-fullscreen class', function () {
                    expect(state.el).not.toHaveClass('video-fullscreen');
                });

                it('tell VideoCaption to resize', function () {
                    expect(videoCaption.resize).toHaveBeenCalled();
                    expect(state.resizer.setMode)
                        .toHaveBeenCalledWith('width');
                });
            });
        });

        describe('play', function () {
            beforeEach(function () {
                initialize();
                spyOn(player, 'playVideo').andCallThrough();
            });

            describe('when the player is not ready', function () {
                beforeEach(function () {
                    player.playVideo = void 0;
                    videoPlayer.play();
                });

                it('does nothing', function () {
                    expect(player.playVideo).toBeUndefined();
                });
            });

            describe('when the player is ready', function () {
                beforeEach(function () {
                    player.playVideo.andReturn(true);
                    videoPlayer.play();
                });

                it('delegate to the player', function () {
                    expect(player.playVideo).toHaveBeenCalled();
                });
            });
        });

        describe('isPlaying', function () {
            beforeEach(function () {
                initialize();
                spyOn(player, 'getPlayerState').andCallThrough();
            });

            describe('when the video is playing', function () {
                beforeEach(function () {
                    player.getPlayerState.andReturn(YT.PlayerState.PLAYING);
                });

                it('return true', function () {
                    expect(videoPlayer.isPlaying()).toBeTruthy();
                });
            });

            describe('when the video is not playing', function () {
                beforeEach(function () {
                    player.getPlayerState.andReturn(YT.PlayerState.PAUSED);
                });

                it('return false', function () {
                    expect(videoPlayer.isPlaying()).toBeFalsy();
                });
            });
        });

        describe('pause', function () {
            beforeEach(function () {
                initialize();
                spyOn(player, 'pauseVideo').andCallThrough();
                videoPlayer.pause();
            });

            it('delegate to the player', function () {
                expect(player.pauseVideo).toHaveBeenCalled();
            });
        });

        describe('duration', function () {
            beforeEach(function () {
                initialize();
                spyOn(player, 'getDuration').andCallThrough();
                videoPlayer.duration();
            });

            it('delegate to the player', function () {
                expect(player.getDuration).toHaveBeenCalled();
            });
        });

        describe('playback rate', function () {
            beforeEach(function () {
                initialize();
                player.setPlaybackRate(1.5);
            });

            it('set the player playback rate', function () {
                expect(player.video.playbackRate).toEqual(1.5);
            });
        });

        describe('volume', function () {
            beforeEach(function () {
                initialize();
                spyOn(player, 'getVolume').andCallThrough();
            });

            it('set the player volume', function () {
                var expectedValue = 60,
                realValue;

                player.setVolume(60);
                realValue = Math.round(player.getVolume()*100);

                expect(realValue).toEqual(expectedValue);
            });
        });

        describe('on Touch devices', function () {
            it('`is-touch` class name is added to container', function () {
                $.each(['iPad', 'Android', 'iPhone'], function(index, device) {
                    window.onTouchBasedDevice.andReturn([device]);
                    initialize();

                    expect(state.el).toHaveClass('is-touch');
                });
            });

            it('modules are not initialized on iPhone', function () {
                window.onTouchBasedDevice.andReturn(['iPhone']);
                initialize();

                var modules = [
                    videoControl, videoCaption, videoProgressSlider,
                    videoSpeedControl, videoVolumeControl
                ];

                $.each(modules, function (index, module) {
                    expect(module).toBeUndefined();
                });
            });

            $.each(['iPad', 'Android'], function(index, device) {
              var message = 'controls become visible after playing starts on ' +
                            device;
              it(message, function() {
                var controls;
                window.onTouchBasedDevice.andReturn([device]);

                runs(function () {
                    initialize();
                    controls = state.el.find('.video-controls');
                });

                waitsFor(function () {
                    return state.el.hasClass('is-initialized');
                },'Video is not initialized.' , WAIT_TIMEOUT);

                runs(function () {
                    expect(controls).toHaveClass('is-hidden');
                    videoPlayer.play();
                });

                waitsFor(function () {
                    duration = videoPlayer.duration();

                    return duration > 0 && videoPlayer.isPlaying();
                },'Video does not play.' , WAIT_TIMEOUT);

                runs(function () {
                    expect(controls).not.toHaveClass('is-hidden');
                });
              });
            });
        });
    });

}).call(this);
