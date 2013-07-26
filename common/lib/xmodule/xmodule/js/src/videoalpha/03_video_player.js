(function (requirejs, require, define) {

// VideoPlayer module.
define(
'videoalpha/03_video_player.js',
['videoalpha/02_html5_video.js'],
function (HTML5Video) {

    // VideoPlayer() function - what this module "exports".
    return function (state) {
        state.videoPlayer = {};

        makeFunctionsPublic(state);
        renderElements(state);
        // No callbacks to DOM events (click, mousemove, etc.).
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function makeFunctionsPublic(state) {
        state.videoPlayer.pause                       = _.bind(pause, state);
        state.videoPlayer.play                        = _.bind(play, state);
        state.videoPlayer.update                      = _.bind(update, state);
        state.videoPlayer.onSpeedChange               = _.bind(onSpeedChange, state);
        state.videoPlayer.onCaptionSeek               = _.bind(onSeek, state);
        state.videoPlayer.onSlideSeek                 = _.bind(onSeek, state);
        state.videoPlayer.onEnded                     = _.bind(onEnded, state);
        state.videoPlayer.onPause                     = _.bind(onPause, state);
        state.videoPlayer.onPlay                      = _.bind(onPlay, state);
        state.videoPlayer.onUnstarted                 = _.bind(onUnstarted, state);
        state.videoPlayer.handlePlaybackQualityChange = _.bind(handlePlaybackQualityChange, state);
        state.videoPlayer.onPlaybackQualityChange     = _.bind(onPlaybackQualityChange, state);
        state.videoPlayer.onStateChange               = _.bind(onStateChange, state);
        state.videoPlayer.onReady                     = _.bind(onReady, state);
        state.videoPlayer.updatePlayTime              = _.bind(updatePlayTime, state);
        state.videoPlayer.isPlaying                   = _.bind(isPlaying, state);
        state.videoPlayer.log                         = _.bind(log, state);
        state.videoPlayer.duration                    = _.bind(duration, state);
        state.videoPlayer.onVolumeChange              = _.bind(onVolumeChange, state);
    }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function renderElements(state) {
        var youTubeId;

        if (state.videoType === 'youtube') {
            state.videoPlayer.PlayerState = YT.PlayerState;
            state.videoPlayer.PlayerState.UNSTARTED = -1;
        } else { // if (state.videoType === 'html5') {
            state.videoPlayer.PlayerState = HTML5Video.PlayerState;
        }

        state.videoPlayer.currentTime = 0;

        state.videoPlayer.playerVars = {
            controls: 0,
            wmode: 'transparent',
            rel: 0,
            showinfo: 0,
            enablejsapi: 1,
            modestbranding: 1
        };

        if (state.currentPlayerMode !== 'flash') {
            state.videoPlayer.playerVars.html5 = 1;
        }

        if (state.config.start) {
            state.videoPlayer.playerVars.start = state.config.start;
            state.videoPlayer.playerVars.wmode = 'window';
        }
        if (state.config.end) {
          state.videoPlayer.playerVars.end = state.config.end;
        }

        // There is a bug which prevents YouTube API to correctly set the speed
        // to 1.0 from another speed in Firefox when in HTML5 mode. There is a
        // fix which basically reloads the video at speed 1.0 when this change
        // is requested (instead of simply requesting a speed change to 1.0).
        // This has to be done only when the video is being watched in Firefox.
        // We need to figure out what browser is currently executing this code.
        //
        // TODO: Check the status of
        // http://code.google.com/p/gdata-issues/issues/detail?id=4654
        // When the YouTube team fixes the API bug, we can remove this temporary
        // bug fix.
        state.browserIsFirefox = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;

        if (state.videoType === 'html5') {
            state.videoPlayer.player = new HTML5Video.Player(state.el, {
                playerVars:   state.videoPlayer.playerVars,
                videoSources: state.html5Sources,
                events: {
                    onReady:       state.videoPlayer.onReady,
                    onStateChange: state.videoPlayer.onStateChange
                }
            });
        } else { // if (state.videoType === 'youtube') {
            if (state.currentPlayerMode === 'flash') {
                youTubeId = state.youtubeId();
            } else {
                youTubeId = state.youtubeId('1.0');
            }
            state.videoPlayer.player = new YT.Player(state.id, {
                playerVars: state.videoPlayer.playerVars,
                videoId: youTubeId,
                events: {
                    onReady: state.videoPlayer.onReady,
                    onStateChange: state.videoPlayer.onStateChange,
                    onPlaybackQualityChange: state.videoPlayer.onPlaybackQualityChange
                }
            });
        }
    }

    // function restartUsingFlash(state)
    //
    //     When we are about to play a YouTube video in HTML5 mode and discover that we only
    //     have one available playback rate, we will switch to Flash mode. In Flash speed
    //     switching is done by reloading videos recorded at different frame rates.
    function restartUsingFlash(state) {
        // Remove from the page current iFrame with HTML5 video.
        state.videoPlayer.player.destroy();

        // Remember for future page loads that we should use Flash mode.
        $.cookie('current_player_mode', 'flash', {
            'expires': 3650,
            'path': '/'
        });
        state.currentPlayerMode = 'flash';

        // Removed configuration option that requests the HTML5 mode.
        delete state.videoPlayer.playerVars.html5;

        // Request for the creation of a new Flash player
        state.videoPlayer.player = new YT.Player(state.id, {
            'playerVars': state.videoPlayer.playerVars,
            'videoId': state.youtubeId(),
            'events': {
                'onReady': state.videoPlayer.onReady,
                'onStateChange': state.videoPlayer.onStateChange,
                'onPlaybackQualityChange': state.videoPlayer.onPlaybackQualityChange
            }
        });
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function pause() {
        if (this.videoPlayer.player.pauseVideo) {
            this.videoPlayer.player.pauseVideo();
        }
    }

    function play() {
        if (this.videoPlayer.player.playVideo) {
            this.videoPlayer.player.playVideo();
        }
    }

    // This function gets the video's current play position in time
    // (currentTime) and its duration.
    // It is called at a regular interval when the video is playing (see below).
    function update() {
        this.videoPlayer.currentTime = this.videoPlayer.player.getCurrentTime();

        if (isFinite(this.videoPlayer.currentTime)) {
            this.videoPlayer.updatePlayTime(this.videoPlayer.currentTime);
        }
    }

    function onSpeedChange(newSpeed, updateCookie) {
        if (this.currentPlayerMode === 'flash') {
            this.videoPlayer.currentTime = Time.convert(
                this.videoPlayer.currentTime,
                parseFloat(this.speed),
                newSpeed
            );
        }
        newSpeed = parseFloat(newSpeed).toFixed(2).replace(/\.00$/, '.0');

        this.videoPlayer.log(
            'speed_change_video',
            {
                current_time: this.videoPlayer.currentTime,
                old_speed: this.speed,
                new_speed: newSpeed
            }
        );

        this.setSpeed(newSpeed, updateCookie);

        if (
            this.currentPlayerMode === 'html5' &&
            !(this.browserIsFirefox && newSpeed === '1.0' && this.videoType === 'youtube')
        ) {
            this.videoPlayer.player.setPlaybackRate(newSpeed);
        } else {
            // We request the reloading of the video in the case when YouTube is in
            // Flash player mode, or when we are in Firefox, and the new speed is 1.0.
            // The second case is necessary to avoid the bug where in Firefox speed
            // switching to 1.0 in HTML5 player mode is handled incorrectly by YouTube
            // API.
            if (this.videoPlayer.isPlaying()) {
                this.videoPlayer.player.loadVideoById(this.youtubeId(), this.videoPlayer.currentTime);
            } else {
                this.videoPlayer.player.cueVideoById(this.youtubeId(), this.videoPlayer.currentTime);
            }

            this.videoPlayer.updatePlayTime(this.videoPlayer.currentTime);
        }
    }

    // Every 200 ms, if the video is playing, we call the function update, via
    // clearInterval. This interval is called updateInterval.
    // It is created on a onPlay event. Cleared on a onPause event.
    // Reinitialized on a onSeek event.
    function onSeek(params) {
        this.videoPlayer.log(
            'seek_video',
            {
                old_time: this.videoPlayer.currentTime,
                new_time: params.time,
                type: params.type
            }
        );

        this.videoPlayer.player.seekTo(params.time, true);

        if (this.videoPlayer.isPlaying()) {
            clearInterval(this.videoPlayer.updateInterval);
            this.videoPlayer.updateInterval = setInterval(this.videoPlayer.update, 200);
        } else {
            this.videoPlayer.currentTime = params.time;
        }

        this.videoPlayer.updatePlayTime(params.time);
    }

    function onEnded() {
        this.trigger('videoControl.pause', null);

        if (this.config.show_captions) {
            this.trigger('videoCaption.pause', null);
        }
    }

    function onPause() {
        this.videoPlayer.log(
            'pause_video',
            {
                'currentTime': this.videoPlayer.currentTime
            }
        );

        clearInterval(this.videoPlayer.updateInterval);
        delete this.videoPlayer.updateInterval;

        this.trigger('videoControl.pause', null);

        if (this.config.show_captions) {
            this.trigger('videoCaption.pause', null);
        }
    }

    function onPlay() {
        this.videoPlayer.log(
            'play_video',
            {
                'currentTime': this.videoPlayer.currentTime
            }
        );

        if (!this.videoPlayer.updateInterval) {
            this.videoPlayer.updateInterval = setInterval(this.videoPlayer.update, 200);
        }

        this.trigger('videoControl.play', null);

        if (this.config.show_captions) {
            this.trigger('videoCaption.play', null);
        }
    }

    function onUnstarted() { }

    function handlePlaybackQualityChange(value) {
        this.videoPlayer.player.setPlaybackQuality(value);
    }

    function onPlaybackQualityChange() {
        var quality;

        quality = this.videoPlayer.player.getPlaybackQuality();

        this.trigger('videoQualityControl.onQualityChange', quality);
    }

    function onReady() {
        var availablePlaybackRates, baseSpeedSubs, _this;

        this.videoPlayer.log('load_video');

        availablePlaybackRates = this.videoPlayer.player.getAvailablePlaybackRates();
        if ((this.currentPlayerMode === 'html5') && (this.videoType === 'youtube')) {
            if (availablePlaybackRates.length === 1) {
                restartUsingFlash(this);

                return;
            } else if (availablePlaybackRates.length > 1) {
                // We need to synchronize available frame rates with the ones
                // that the user specified.

                baseSpeedSubs = this.videos['1.0'];
                _this = this;
                // this.videos is a dictionary containing various frame rates
                // and their associated subs.

                // First clear the dictionary.
                $.each(this.videos, function(index, value) {
                    delete _this.videos[index];
                });
                this.speeds = [];
                // Recreate it with the supplied frame rates.
                $.each(availablePlaybackRates, function(index, value) {
                    _this.videos[value.toFixed(2).replace(/\.00$/, '.0')] = baseSpeedSubs;

                    _this.speeds.push(value.toFixed(2).replace(/\.00$/, '.0'));
                });

                this.trigger('videoSpeedControl.reRender', {'newSpeeds': this.speeds, 'currentSpeed': this.speed});

                this.setSpeed($.cookie('video_speed'));
            }
        }

        if (this.currentPlayerMode === 'html5') {
            this.videoPlayer.player.setPlaybackRate(this.speed);
        }

        if (!onTouchBasedDevice() && $('.videoalpha:first').data('autoplay') === 'True') {
            this.videoPlayer.play();
        }
    }

    function onStateChange(event) {
        switch (event.data) {
            case this.videoPlayer.PlayerState.UNSTARTED:
                this.videoPlayer.onUnstarted();
                break;
            case this.videoPlayer.PlayerState.PLAYING:
                this.videoPlayer.onPlay();
                break;
            case this.videoPlayer.PlayerState.PAUSED:
                this.videoPlayer.onPause();
                break;
            case this.videoPlayer.PlayerState.ENDED:
                this.videoPlayer.onEnded();
                break;
        }
    }

    function updatePlayTime(time) {
        var duration;

        duration = this.videoPlayer.duration();

        this.trigger('videoProgressSlider.updatePlayTime', {'time': time, 'duration': duration});
        this.trigger('videoControl.updateVcrVidTime', {'time': time, 'duration': duration});
        this.trigger('videoCaption.updatePlayTime', time);
    }

    function isPlaying() {
        return this.videoPlayer.player.getPlayerState() === this.videoPlayer.PlayerState.PLAYING;
    }

    function duration() {
        var dur;

        dur = this.videoPlayer.player.getDuration();
        if (!isFinite(dur)) {
            dur = this.getDuration();
        }

        return dur;
    }

    function log(eventName, data) {
        var logInfo;

        // Default parameters that always get logged.
        logInfo = {
            'id':   this.id,
            'code': this.youtubeId()
        };

        // If extra parameters were passed to the log.
        if (data) {
            $.each(data, function(paramName, value) {
                logInfo[paramName] = value;
            });
        }

        if (this.videoType === 'youtube') {
            logInfo.code = this.youtubeId();
        } else  if (this.videoType === 'html5') {
                logInfo.code = 'html5';
        }

        Logger.log(eventName, logInfo);
    }

    function onVolumeChange(volume) {
        this.videoPlayer.player.setVolume(volume);
    }
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
