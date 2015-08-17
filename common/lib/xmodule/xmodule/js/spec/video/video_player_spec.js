(function (requirejs, require, define, undefined) {
'use strict';

require(
['video/03_video_player.js'],
function (VideoPlayer) {
    describe('VideoPlayer', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                .andReturn(null);
        });

        afterEach(function () {
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

        describe('constructor', function () {
            describe('always', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    state.videoEl = $('video, iframe');
                });

                it('instanticate current time to zero', function () {
                    expect(state.videoPlayer.currentTime).toEqual(0);
                });

                it('set the element', function () {
                    expect(state.el).toHaveId('video_id');
                });

                it('create video control', function () {
                    expect(state.videoControl).toBeDefined();
                    expect(state.videoControl.el).toHaveClass('video-controls');
                });

                it('create video caption', function () {
                    expect(state.videoCaption).toBeDefined();
                    expect(state.speed).toEqual('1.50');
                    expect(state.config.transcriptTranslationUrl)
                        .toEqual('/transcript/translation/__lang__');
                });

                it('create video speed control', function () {
                    expect(state.videoSpeedControl).toBeDefined();
                    expect(state.videoSpeedControl.el).toHaveClass('speeds');
                    expect(state.speed).toEqual('1.50');
                });

                it('create video progress slider', function () {
                    expect(state.videoProgressSlider).toBeDefined();
                    expect(state.videoProgressSlider.el).toHaveClass('slider');
                });

                // All the toHandleWith() expect tests are not necessary for
                // this version of Video. jQuery event system is not used to
                // trigger and invoke methods. This is an artifact from
                // previous version of Video.
            });

            it('create Youtube player', function () {
                var events;

                jasmine.stubRequests();
                spyOn(window.YT, 'Player').andCallThrough();
                state = jasmine.initializePlayerYouTube();
                state.videoEl = $('video, iframe');

                events = {
                    onReady:                 state.videoPlayer.onReady,
                    onStateChange:           state.videoPlayer.onStateChange,
                    onPlaybackQualityChange: state.videoPlayer.onPlaybackQualityChange,
                    onError:                 state.videoPlayer.onError
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
            });

            it('create Flash player', function () {
                var player;

                spyOn($.fn, 'trigger');
                state = jasmine.initializePlayerYouTube();
                state.videoEl = state.el.find('video, iframe').width(100);
                player = state.videoPlayer.player;
                player.getAvailablePlaybackRates.andReturn([1]);
                state.currentPlayerMode = 'html5';
                spyOn(window.YT, 'Player').andCallThrough();
                state.videoPlayer.onReady();

                expect(YT.Player).toHaveBeenCalledWith('id', {
                    playerVars: {
                        controls: 0,
                        wmode: 'transparent',
                        rel: 0,
                        showinfo: 0,
                        enablejsapi: 1,
                        modestbranding: 1
                    },
                    videoId: 'abcdefghijkl',
                    events: jasmine.any(Object)
                });

                expect(state.resizer.setElement).toHaveBeenCalled();
                expect(state.resizer.align).toHaveBeenCalled();
            });

            // We can't test the invocation of HTML5Video because it is not
            // available globally. It is defined within the scope of Require
            // JS.

            describe('when on a touch based device', function () {
                $.each(['iPad', 'Android'], function (index, device) {
                    it('create video volume control on' + device, function () {
                        window.onTouchBasedDevice.andReturn([device]);
                        state = jasmine.initializePlayer();

                        state.videoEl = $('video, iframe');

                        expect(state.el.find('.volume')).not.toExist();
                    });
                });
            });

            describe('when not on a touch based device', function () {
                var oldOTBD;

                beforeEach(function () {
                    state = jasmine.initializePlayer();

                    state.videoEl = $('video, iframe');
                });

                it('controls are in paused state', function () {
                    expect(state.videoPlayer.isPlaying()).toBe(false);
                });
            });
        });

        describe('onReady', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();

                state.videoEl = $('video, iframe');
                spyOn(state.videoPlayer, 'play').andCallThrough();
                state.videoPlayer.onReady();
            });

            it('autoplay the first video', function () {
                expect(state.videoPlayer.play).not.toHaveBeenCalled();
            });


            it('invalid endTime is reset to null', function () {
                expect(state.videoPlayer.endTime).toBe(null);
            });
        });

        describe('onReady YouTube', function () {
            beforeEach(function () {
                state = jasmine.initializePlayerYouTube();

                state.videoEl = $('video, iframe');
            });

            it('multiple speeds and flash mode, change back to html5 mode', function () {
                var playbackRates = state.videoPlayer.player.getAvailablePlaybackRates();

                state.currentPlayerMode = 'flash';
                state.videoPlayer.onReady();
                expect(playbackRates.length).toBe(4);
                expect(state.currentPlayerMode).toBe('html5');
            });
        });

        describe('onStateChange Youtube', function(){
            describe('when the video is ended', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayerYouTube();

                    state.videoEl = $('video, iframe');
                    spyOn($.fn, 'trigger').andCallThrough();
                    state.videoPlayer.onStateChange({
                        data: YT.PlayerState.ENDED
                    });
                });

                it('pause the video control', function () {
                    expect($('.video_control')).toHaveClass('play');
                });

                it('trigger pause and ended events', function () {
                    expect($.fn.trigger).toHaveBeenCalledWith('pause', {});
                    expect($.fn.trigger).toHaveBeenCalledWith('ended', {});
                });
            });
        });

        describe('onStateChange', function () {
            describe('when the video is unstarted', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    state.videoEl = $('video, iframe');
                    spyOn($.fn, 'trigger').andCallThrough();

                    state.videoPlayer.onStateChange({
                        data: YT.PlayerState.PAUSED
                    });
                });

                it('pause the video control', function () {
                    expect($('.video_control')).toHaveClass('play');
                });

                it('pause the video caption', function () {
                    expect($.fn.trigger).toHaveBeenCalledWith('pause', {});
                });
            });

            describe('when the video is playing', function () {
                var oldState;

                beforeEach(function () {
                    // Create the first instance of the player.
                    state = jasmine.initializePlayer();
                    oldState = state;

                    spyOn(oldState.videoPlayer, 'onPause').andCallThrough();

                    // Now initialize a second instance.
                    state = jasmine.initializePlayer();

                    state.videoEl = $('video, iframe');

                    spyOn(window, 'setInterval').andReturn(100);
                    spyOn($.fn, 'trigger').andCallThrough();

                    state.videoPlayer.onStateChange({
                        data: YT.PlayerState.PLAYING
                    });
                });

                it('set update interval', function () {
                    expect(window.setInterval).toHaveBeenCalledWith(
                        state.videoPlayer.update, 200
                    );
                    expect(state.videoPlayer.updateInterval).toEqual(100);
                });

                it('play the video control', function () {
                    expect($('.video_control')).toHaveClass('pause');
                });

                it('play the video caption', function () {
                    expect($.fn.trigger).toHaveBeenCalledWith('play', {});
                });
            });

            describe('when the video is paused', function () {
                var currentUpdateIntrval;

                beforeEach(function () {
                    state = jasmine.initializePlayer();

                    state.videoEl = $('video, iframe');

                    spyOn($.fn, 'trigger').andCallThrough();
                    state.videoPlayer.onStateChange({
                        data: YT.PlayerState.PLAYING
                    });

                    currentUpdateIntrval = state.videoPlayer.updateInterval;

                    state.videoPlayer.onStateChange({
                        data: YT.PlayerState.PAUSED
                    });
                });

                it('clear update interval', function () {
                    expect(state.videoPlayer.updateInterval).toBeUndefined();
                });

                it('pause the video control', function () {
                    expect($('.video_control')).toHaveClass('play');
                });

                it('pause the video caption', function () {
                    expect($.fn.trigger).toHaveBeenCalledWith('pause', {});
                });
            });

            describe('when the video is ended', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();

                    state.videoEl = $('video, iframe');
                    spyOn($.fn, 'trigger').andCallThrough();
                    state.videoPlayer.onStateChange({
                        data: YT.PlayerState.ENDED
                    });
                });

                it('pause the video control', function () {
                    expect($('.video_control')).toHaveClass('play');
                });

                it('pause the video caption', function () {
                    expect($.fn.trigger).toHaveBeenCalledWith('ended', {});
                });
            });
        });

        describe('onSeek', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                state.videoEl = $('video, iframe');
                jasmine.Clock.useMock();
                spyOn(state.videoPlayer, 'duration').andReturn(120);
            });

            describe('when the video is playing', function () {
                beforeEach(function () {
                    runs(function () {
                        state.videoPlayer.play();
                    });

                    waitsFor(function () {
                        return state.videoPlayer.isPlaying();
                    }, 'video didn\'t start playing', WAIT_TIMEOUT);
                });


                it('call runTimer in seekTo on player', function () {
                    runs(function () {
                        spyOn(state.videoPlayer, 'stopTimer');
                        spyOn(state.videoPlayer, 'runTimer');
                        state.videoPlayer.seekTo(10);
                        // Video player uses _.debounce (with a wait time in 300 ms) for seeking.
                        // That's why we have to do this tick(300).
                        jasmine.Clock.tick(300);
                        expect(state.videoPlayer.currentTime).toBe(10);
                        expect(state.videoPlayer.stopTimer).toHaveBeenCalled();
                        expect(state.videoPlayer.runTimer).toHaveBeenCalled();
                    });
                });

                it('seek the player', function () {
                    runs(function () {
                        spyOn(state.videoPlayer.player, 'seekTo').andCallThrough();
                        state.videoProgressSlider.onSlide(
                            jQuery.Event('slide'), { value: 30 }
                        );
                        // Video player uses _.debounce (with a wait time in 300 ms) for seeking.
                        // That's why we have to do this tick(300).
                        jasmine.Clock.tick(300);
                        expect(state.videoPlayer.currentTime).toBe(30);
                        expect(state.videoPlayer.player.seekTo).toHaveBeenCalledWith(30, true);
                    });
                });

                it('call updatePlayTime on player', function () {
                    runs(function () {
                        spyOn(state.videoPlayer, 'updatePlayTime').andCallThrough();
                        state.videoProgressSlider.onSlide(
                            jQuery.Event('slide'), { value: 30 }
                        );
                        // Video player uses _.debounce (with a wait time in 300 ms) for seeking.
                        // That's why we have to do this tick(300).
                        jasmine.Clock.tick(300);
                        expect(state.videoPlayer.currentTime).toBe(30);
                        expect(state.videoPlayer.updatePlayTime).toHaveBeenCalledWith(30, true);
                    });
                });
            });

            it('when the player is not playing: set the current time', function () {
                state.videoProgressSlider.onSlide(
                    jQuery.Event('slide'), { value: 20 }
                );
                // Video player uses _.debounce (with a wait time in 300 ms) for seeking.
                // That's why we have to do this tick(300).
                jasmine.Clock.tick(300);
                state.videoPlayer.pause();
                expect(state.videoPlayer.currentTime).toBe(20);
                state.videoProgressSlider.onSlide(
                    jQuery.Event('slide'), { value: 10 }
                );
                // Video player uses _.debounce (with a wait time in 300 ms) for seeking.
                // That's why we have to do this tick(300).
                jasmine.Clock.tick(300);
                expect(state.videoPlayer.currentTime).toBe(10);
            });

            describe('when the video is not playing', function () {
                beforeEach(function () {
                    spyOn(state.videoPlayer, 'setPlaybackRate')
                        .andCallThrough();
                });

                it('video has a correct speed', function () {
                    state.speed = '2.0';
                    state.videoPlayer.onPlay();
                    expect(state.videoPlayer.setPlaybackRate)
                        .toHaveBeenCalledWith('2.0', true);
                    state.videoPlayer.onPlay();
                    expect(state.videoPlayer.setPlaybackRate.calls.length)
                        .toEqual(1);
                });
            });
        });

        describe('onVolumeChange', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                state.videoPlayer.onReady();
                state.videoEl = $('video, iframe');
            });

            it('set the volume on player', function () {
                spyOn(state.videoPlayer.player, 'setVolume');
                state.videoPlayer.onVolumeChange(60);
                expect(state.videoPlayer.player.setVolume)
                    .toHaveBeenCalledWith(60);
            });

            describe('when the video is not playing', function () {
                beforeEach(function () {
                    state.videoPlayer.player.setVolume('1');
                });

                it('video has a correct volume', function () {
                    spyOn(state.videoPlayer.player, 'setVolume');
                    state.videoVolumeControl.volume = 26;
                    state.el.trigger('play');
                    expect(state.videoPlayer.player.setVolume)
                        .toHaveBeenCalledWith(26);
                });
            });
        });

        describe('update', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();

                state.videoEl = $('video, iframe');

                spyOn(state.videoPlayer, 'updatePlayTime').andCallThrough();
            });

            describe(
                'when the current time is unavailable from the player',
                function ()
            {
                beforeEach(function () {
                    state.videoPlayer.player.getCurrentTime = function () {
                        return NaN;
                    };
                    state.videoPlayer.update();
                });

                it('does not trigger updatePlayTime event', function () {
                    expect(state.videoPlayer.updatePlayTime)
                        .not.toHaveBeenCalled();
                });
            });

            describe(
                'when the current time is available from the player',
                function ()
            {
                beforeEach(function () {
                    state.videoPlayer.player.getCurrentTime = function () {
                        return 60;
                    };
                    state.videoPlayer.update();
                });

                it('trigger updatePlayTime event', function () {
                    expect(state.videoPlayer.updatePlayTime)
                        .toHaveBeenCalledWith(60);
                });
            });
        });

        // Disabled 1/13/14 due to flakiness observed in master
        xdescribe('update with start & end time', function () {
            var START_TIME = 1, END_TIME = 2;

            beforeEach(function () {
                state = jasmine.initializePlayer(
                    {
                        start: START_TIME,
                        end: END_TIME
                    }
                );

                state.videoEl = $('video, iframe');

                spyOn(state.videoPlayer, 'update').andCallThrough();
                spyOn(state.videoPlayer, 'pause').andCallThrough();
                spyOn(state.videoProgressSlider, 'notifyThroughHandleEnd')
                    .andCallThrough();
            });

            it(
                'video is paused on first endTime, start & end time are reset',
                function ()
            {
                var duration;

                state.videoProgressSlider.notifyThroughHandleEnd.reset();
                state.videoPlayer.pause.reset();
                state.videoPlayer.play();

                waitsFor(function () {
                    duration = Math.round(state.videoPlayer.currentTime);

                    return state.videoPlayer.pause.calls.length === 1;
                }, 'pause() has been called', WAIT_TIMEOUT);

                runs(function () {
                    expect(state.videoPlayer.startTime).toBe(0);
                    expect(state.videoPlayer.endTime).toBe(null);

                    expect(duration).toBe(END_TIME);

                    expect(state.videoProgressSlider.notifyThroughHandleEnd)
                        .toHaveBeenCalledWith({end: true});
                });
            });
        });

        describe('updatePlayTime', function () {
            beforeEach(function () {
                state = jasmine.initializePlayerYouTube();
                state.videoEl = $('video, iframe');
                spyOn(state.videoCaption, 'updatePlayTime').andCallThrough();
                spyOn(state.videoProgressSlider, 'updatePlayTime').andCallThrough();
            });

            it('update the video playback time', function () {
                var duration = 0;

                waitsFor(function () {
                    duration = state.videoPlayer.duration();

                    if (duration > 0) {
                        return true;
                    }

                    return false;
                }, 'Video is fully loaded.', WAIT_TIMEOUT);

                runs(function () {
                    state.videoPlayer.goToStartTime = false;
                    state.videoPlayer.updatePlayTime(60);

                    expect($('.vidtime')).toHaveHtml('1:00 / 1:00');
                });
            });

            it('update the playback time on caption', function () {
                waitsFor(function () {
                    return state.videoPlayer.duration() > 0;
                }, 'Video is fully loaded.', WAIT_TIMEOUT);

                runs(function () {
                    state.videoPlayer.goToStartTime = false;
                    state.videoPlayer.updatePlayTime(60);

                    expect(state.videoCaption.updatePlayTime)
                        .toHaveBeenCalledWith(60);
                });
            });

            it('update the playback time on progress slider', function () {
                var duration = 0;

                waitsFor(function () {
                    duration = state.videoPlayer.duration();

                    return duration > 0;
                }, 'Video is fully loaded.', WAIT_TIMEOUT);

                runs(function () {
                    state.videoPlayer.goToStartTime = false;
                    state.videoPlayer.updatePlayTime(60);

                    expect(state.videoProgressSlider.updatePlayTime)
                        .toHaveBeenCalledWith({
                            time: 60,
                            duration: duration
                        });
                });
            });
        });

        // Disabled 1/13/14 due to flakiness observed in master
        xdescribe(
            'updatePlayTime when start & end times are defined',
            function ()
        {
            var START_TIME = 1,
                END_TIME = 2;

            beforeEach(function () {
                state = jasmine.initializePlayer(
                    {
                        start: START_TIME,
                        end: END_TIME
                    }
                );

                state.videoEl = $('video, iframe');

                spyOn(state.videoPlayer, 'updatePlayTime').andCallThrough();
                spyOn(state.videoPlayer.player, 'seekTo').andCallThrough();
                spyOn(state.videoProgressSlider, 'updateStartEndTimeRegion')
                    .andCallThrough();
            });

            it(
                'when duration becomes available, updatePlayTime() is called',
                function ()
            {
                var duration;

                expect(state.videoPlayer.initialSeekToStartTime).toBeTruthy();
                expect(state.videoPlayer.seekToStartTimeOldSpeed).toBe('void');

                state.videoPlayer.play();

                waitsFor(function () {
                    duration = state.videoPlayer.duration();

                    return state.videoPlayer.isPlaying() &&
                        state.videoPlayer.initialSeekToStartTime === false;
                }, 'duration becomes available', WAIT_TIMEOUT);

                runs(function () {
                    expect(state.videoPlayer.startTime).toBe(START_TIME);
                    expect(state.videoPlayer.endTime).toBe(END_TIME);

                    expect(state.videoPlayer.player.seekTo)
                        .toHaveBeenCalledWith(START_TIME);

                    expect(state.videoProgressSlider.updateStartEndTimeRegion)
                        .toHaveBeenCalledWith({duration: duration});

                    expect(state.videoPlayer.seekToStartTimeOldSpeed)
                        .toBe(state.speed);
                });
            });
        });

        describe('updatePlayTime with invalid endTime', function () {
            beforeEach(function () {
                state = {
                    el: $('#video_id'),
                    videoPlayer: {
                        duration: function () {
                            // The video will be 60 seconds long.
                            return 60;
                        },
                        goToStartTime: true,
                        startTime: undefined,
                        endTime: undefined,
                        player: {
                            seekTo: function () {}
                        },
                        figureOutStartEndTime: jasmine.createSpy(),
                        figureOutStartingTime: jasmine.createSpy().andReturn(0)
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
                    trigger: function () {},
                    browserIsFirefox: false,
                    isFlashMode: jasmine.createSpy().andReturn(false)
                };
            });
        });

        describe('toggleFullScreen', function () {
            describe('when the video player is not full screen', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    state.videoEl = $('video, iframe');
                    spyOn($.fn, 'trigger').andCallThrough();
                    $('.add-fullscreen').click();
                });

                it('replace the full screen button tooltip', function () {
                    expect($('.add-fullscreen'))
                        .toHaveAttr('title', 'Exit full browser');
                });

                it('add the video-fullscreen class', function () {
                    expect(state.el).toHaveClass('video-fullscreen');
                });

                it('tell VideoCaption to resize', function () {
                    expect($.fn.trigger).toHaveBeenCalledWith('fullscreen', [true]);
                    expect(state.resizer.setMode).toHaveBeenCalledWith('both');
                    expect(state.resizer.delta.substract).toHaveBeenCalled();
                });
            });

            describe('when the video player already full screen', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    state.videoEl = $('video, iframe');
                    spyOn($.fn, 'trigger').andCallThrough();
                    state.el.addClass('video-fullscreen');
                    state.videoFullScreen.fullScreenState = true;
                    state.videoFullScreen.isFullScreen = true;
                    state.videoFullScreen.fullScreenEl.attr('title', 'Exit-fullscreen');
                    $('.add-fullscreen').click();
                });

                it('replace the full screen button tooltip', function () {
                    expect($('.add-fullscreen'))
                        .toHaveAttr('title', 'Fill browser');
                });

                it('remove the video-fullscreen class', function () {
                    expect(state.el).not.toHaveClass('video-fullscreen');
                });

                it('tell VideoCaption to resize', function () {
                    expect($.fn.trigger).toHaveBeenCalledWith('fullscreen', [false]);
                    expect(state.resizer.setMode)
                        .toHaveBeenCalledWith('width');
                    expect(state.resizer.delta.reset).toHaveBeenCalled();
                });
            });
        });

        describe('duration', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();

                state.videoEl = $('video, iframe');

                spyOn(state.videoPlayer.player, 'getDuration').andCallThrough();
                state.videoPlayer.duration();
            });

            it('delegate to the player', function () {
                expect(state.videoPlayer.player.getDuration).toHaveBeenCalled();
            });
        });

        describe('getDuration', function () {
            beforeEach(function () {
                // We need to make sure that metadata is returned via an AJAX
                // request. Without the jasmine.stubRequests() below we will
                // get the error:
                //
                //     this.metadata[this.youtubeId(...)] is undefined
                jasmine.stubRequests();

                state = jasmine.initializePlayerYouTube();

                state.videoEl = $('video, iframe');

                spyOn(state, 'getDuration').andCallThrough();

                // When `state.videoPlayer.player.getDuration()` returns a `0`,
                // the fall-back function `state.getDuration()` will be called.
                state.videoPlayer.player.getDuration.andReturn(0);
            });

            it('getDuration is called as a fall-back', function () {
                state.videoPlayer.duration();

                expect(state.getDuration).toHaveBeenCalled();
            });
        });

        describe('volume', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();

                state.videoEl = $('video, iframe');

                spyOn(state.videoPlayer.player, 'getVolume').andCallThrough();
            });

            it('set the player volume', function () {
                var expectedValue = 60,
                realValue;

                state.videoPlayer.player.setVolume(60);
                realValue = Math.round(state.videoPlayer.player.getVolume()*100);

                expect(realValue).toEqual(expectedValue);
            });
        });

        describe('on Touch devices', function () {
            it('`is-touch` class name is added to container', function () {
                $.each(
                    ['iPad', 'Android', 'iPhone'],
                    function (index, device)
                {
                    window.onTouchBasedDevice.andReturn([device]);
                    state = jasmine.initializePlayer();

                    state.videoEl = $('video, iframe');

                    expect(state.el).toHaveClass('is-touch');
                });
            });

            it('modules are not initialized on iPhone', function () {
                window.onTouchBasedDevice.andReturn(['iPhone']);
                state = jasmine.initializePlayer();

                state.videoEl = $('video, iframe');

                var modules = [
                    state.videoControl, state.videoCaption, state.videoProgressSlider,
                    state.videoSpeedControl, state.videoVolumeControl
                ];

                $.each(modules, function (index, module) {
                    expect(module).toBeUndefined();
                });
            });

            $.each(['iPad', 'Android'], function (index, device) {
                var message = 'controls become visible after playing starts ' +
                    'on ' + device;

                it(message, function () {
                    var controls;

                    window.onTouchBasedDevice.andReturn([device]);

                    runs(function () {
                        state = jasmine.initializePlayer();
                        state.videoEl = $('video, iframe');
                        controls = state.el.find('.video-controls');
                    });

                    waitsFor(function () {
                        return state.el.hasClass('is-initialized');
                    },'Video is not initialized.' , WAIT_TIMEOUT);

                    runs(function () {
                        expect(controls).toHaveClass('is-hidden');
                        state.videoPlayer.play();
                    });

                    waitsFor(function () {
                        var duration = state.videoPlayer.duration();

                        return duration > 0 && state.videoPlayer.isPlaying();
                    },'Video does not play.' , WAIT_TIMEOUT);

                    runs(function () {
                        expect(controls).not.toHaveClass('is-hidden');
                    });
                });
            });
        });

        describe('onSpeedChange', function () {
            beforeEach(function () {
                state = {
                    el: $(document),
                    speed: '1.50',
                    setSpeed: jasmine.createSpy(),
                    saveState: jasmine.createSpy(),
                    videoPlayer: {
                        currentTime: 60,
                        updatePlayTime: jasmine.createSpy(),
                        setPlaybackRate: jasmine.createSpy(),
                        player: jasmine.createSpyObj('player', ['setPlaybackRate'])
                    },
                    isFlashMode: jasmine.createSpy().andReturn(false)
                };
            });

            describe('always', function () {
                it('convert the current time to the new speed', function () {
                    state.isFlashMode.andReturn(true);
                    VideoPlayer.prototype.onSpeedChange.call(state, '0.75', false);
                    expect(state.videoPlayer.currentTime).toBe('120.000');
                });

                it('set video speed to the new speed', function () {
                    VideoPlayer.prototype.onSpeedChange.call(state, '0.75', false);
                    expect(state.setSpeed).toHaveBeenCalledWith('0.75');
                    expect(state.videoPlayer.setPlaybackRate)
                        .toHaveBeenCalledWith('0.75');
                });
            });
        });

        describe('setPlaybackRate', function () {
            beforeEach(function () {
                state = {
                    youtubeId: jasmine.createSpy().andReturn('videoId'),
                    isFlashMode: jasmine.createSpy().andReturn(false),
                    isHtml5Mode: jasmine.createSpy().andReturn(true),
                    isYoutubeType: jasmine.createSpy().andReturn(true),
                    setPlayerMode: jasmine.createSpy(),
                    trigger: jasmine.createSpy(),
                    videoPlayer: {
                        currentTime: 60,
                        isPlaying: jasmine.createSpy(),
                        seekTo: jasmine.createSpy(),
                        duration: jasmine.createSpy().andReturn(60),
                        updatePlayTime: jasmine.createSpy(),
                        setPlaybackRate: jasmine.createSpy(),
                        player: jasmine.createSpyObj('player', [
                            'setPlaybackRate', 'loadVideoById', 'cueVideoById'
                        ])
                    }
                };
            });

            it('in Flash mode and video is playing', function () {
                state.isFlashMode.andReturn(true);
                state.isHtml5Mode.andReturn(false);
                state.videoPlayer.isPlaying.andReturn(true);
                VideoPlayer.prototype.setPlaybackRate.call(state, '0.75');
                expect(state.videoPlayer.updatePlayTime).toHaveBeenCalledWith(60);
                expect(state.videoPlayer.player.loadVideoById)
                    .toHaveBeenCalledWith('videoId', 60);
            });

            it('in Flash mode and video not started', function () {
                state.isFlashMode.andReturn(true);
                state.isHtml5Mode.andReturn(false);
                state.videoPlayer.isPlaying.andReturn(false);
                VideoPlayer.prototype.setPlaybackRate.call(state, '0.75');
                expect(state.videoPlayer.updatePlayTime).toHaveBeenCalledWith(60);
                expect(state.videoPlayer.seekTo).toHaveBeenCalledWith(60);
                expect(state.trigger).toHaveBeenCalledWith(
                    'videoProgressSlider.updateStartEndTimeRegion',
                    {
                        duration: 60
                    });
                expect(state.videoPlayer.player.cueVideoById)
                    .toHaveBeenCalledWith('videoId', 60);
            });

            it('in HTML5 mode', function () {
                state.isYoutubeType.andReturn(false);
                VideoPlayer.prototype.setPlaybackRate.call(state, '0.75');
                expect(state.videoPlayer.player.setPlaybackRate).toHaveBeenCalledWith('0.75');
            });

            it('Youtube video in FF, with new speed equal 1.0', function () {
                state.browserIsFirefox = true;

                state.videoPlayer.isPlaying.andReturn(false);
                VideoPlayer.prototype.setPlaybackRate.call(state, '1.0');
                expect(state.videoPlayer.updatePlayTime).toHaveBeenCalledWith(60);
                expect(state.videoPlayer.player.cueVideoById)
                    .toHaveBeenCalledWith('videoId', 60);
            });
        });
    });
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
