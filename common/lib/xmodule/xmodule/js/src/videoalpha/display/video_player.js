(function (requirejs, require, define) {

// VideoPlayer module.
define(
'videoalpha/display/video_player.js',
['videoalpha/display/html5_video.js', 'videoalpha/display/bind.js'],
function (HTML5Video, bind) {

    // VideoPlayer() function - what this module "exports".
    return function (state) {
        state.videoPlayer = {};

        // Functions which will be accessible via 'state' object.
        makeFunctionsPublic(state);

        if (state.videoType === 'youtube') {
          state.videoPlayer.PlayerState = YT.PlayerState;
          state.videoPlayer.PlayerState.UNSTARTED = -1;
        } else { // if (state.videoType === 'html5') {
          state.videoPlayer.PlayerState = HTML5Video.PlayerState;
        }
        state.videoPlayer.currentTime = 0;

        renderElements(state);
        bindHandlers();
    };

    // Private functions start here.

    function makeFunctionsPublic(state) {
        state.videoPlayer.pause                       = bind(pause, state);
        state.videoPlayer.play                        = bind(play, state);
        state.videoPlayer.toggleFullScreen            = bind(toggleFullScreen, state);
        state.videoPlayer.update                      = bind(update, state);
        state.videoPlayer.onVolumeChange              = bind(onVolumeChange, state);
        state.videoPlayer.onSpeedChange               = bind(onSpeedChange, state);
        state.videoPlayer.onSeek                      = bind(onSeek, state);
        state.videoPlayer.onEnded                     = bind(onEnded, state);
        state.videoPlayer.onPause                     = bind(onPause, state);
        state.videoPlayer.onPlay                      = bind(onPlay, state);
        state.videoPlayer.onUnstarted                 = bind(onUnstarted, state);
        state.videoPlayer.handlePlaybackQualityChange = bind(handlePlaybackQualityChange, state);
        state.videoPlayer.onPlaybackQualityChange     = bind(onPlaybackQualityChange, state);
        state.videoPlayer.onStateChange               = bind(onStateChange, state);
        state.videoPlayer.onReady                     = bind(onReady, state);
        state.videoPlayer.bindExitFullScreen          = bind(bindExitFullScreen, state);
    }

    function renderElements(state) {
        var youTubeId;

        state.videoPlayer.playerVars = {
            'controls': 0,
            'wmode': 'transparent',
            'rel': 0,
            'showinfo': 0,
            'enablejsapi': 1,
            'modestbranding': 1
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

        if (state.videoType === 'html5') {
            state.videoPlayer.player = new HTML5Video.Player(state.el, {
                'playerVars':   state.videoPlayer.playerVars,
                'videoSources': state.html5Sources,
                'events': {
                    'onReady':       state.videoPlayer.onReady,
                    'onStateChange': state.videoPlayer.onStateChange
                }
            });
        } else if (state.videoType === 'youtube') {
            if (state.currentPlayerMode === 'flash') {
                youTubeId = state.youtubeId();
            } else {
                youTubeId = state.youtubeId('1.0');
            }
            state.videoPlayer.player = new YT.Player(state.id, {
                'playerVars': state.videoPlayer.playerVars,
                'videoId': youTubeId,
                'events': {
                    'onReady': state.videoPlayer.onReady,
                    'onStateChange': state.videoPlayer.onStateChange,
                    'onPlaybackQualityChange': state.videoPlayer.onPlaybackQualityChange
                }
            });
        }
    }

    function bindHandlers() {

    }

    function reinitAsFlash(state) {
        state.videoPlayer.player.destroy();

        $.cookie('current_player_mode', 'flash', {
            expires: 3650,
            path: '/'
        });
        state.currentPlayerMode = 'flash';

        delete state.videoPlayer.playerVars.html5;

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

    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().

    function pause() { }

    function play() {
        if (this.videoPlayer.player.playVideo) {
            this.videoPlayer.player.playVideo();
        }

        console.log('state is:');
        console.log(this);
    }

    function toggleFullScreen() { }

    function update() { }

    function onVolumeChange() { }

    function onSpeedChange() { }

    function onSeek() { }

    function onEnded() {
        console.log('this.videoPlayer.PlayerState.ENDED');
    }

    function onPause() {
        console.log('this.videoPlayer.PlayerState.PAUSED');
    }

    function onPlay() {
        console.log('this.videoPlayer.PlayerState.PLAYING');
    }

    function onUnstarted() {
        console.log('this.videoPlayer.PlayerState.UNSTARTED');
    }

    function handlePlaybackQualityChange() { }

    function onPlaybackQualityChange() { }

    function onReady() {
        var availablePlaybackRates, baseSpeedSubs, _this;

        console.log('We are in ready function.');

        availablePlaybackRates = this.videoPlayer.player.getAvailablePlaybackRates();
        if ((this.currentPlayerMode === 'html5') && (this.videoType === 'youtube')) {
            if (availablePlaybackRates.length === 1) {
                console.log('We are playing YouTube video in HTML5 mode but have only one speed. Will reload in Flash mode.');
                reinitAsFlash(this);

                return;
            } else if (availablePlaybackRates.length > 1) {
                // We need to synchronize available frame rates with the ones that the user specified.
                console.log('We are a YouTube video in HTML5 player mode.');

                baseSpeedSubs = this.videos['1.0'];
                _this = this;
                $.each(this.videos, function(index, value) {
                    delete _this.videos[index];
                });
                this.speeds = [];
                $.each(availablePlaybackRates, function(index, value) {
                    _this.videos[value.toFixed(2).replace(/\.00$/, '.0')] = baseSpeedSubs;
                    _this.speeds.push(value.toFixed(2).replace(/\.00$/, '.0'));
                });

                this.setSpeed($.cookie('video_speed'));
            }
        }

        if (this.currentPlayerMode === 'html5') {
            this.videoPlayer.player.setPlaybackRate(this.speed);
        }

        if (!onTouchBasedDevice()) {
            this.videoPlayer.play();
        }
    }

    function onStateChange() {
        console.log('function onStateChange()');
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

    function bindExitFullScreen() { }
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));



/*

    VideoPlayerAlpha.prototype.bind = function() {
      $(this.control).bind('play', this.play).bind('pause', this.pause);
      if (this.video.videoType === 'youtube') {
        $(this.qualityControl).bind('changeQuality', this.handlePlaybackQualityChange);
      }
      if (this.video.show_captions === true) {
        $(this.caption).bind('seek', this.onSeek);
      }
      $(this.speedControl).bind('speedChange', this.onSpeedChange);
      $(this.progressSlider).bind('seek', this.onSeek);
      if (this.volumeControl) {
        $(this.volumeControl).bind('volumeChange', this.onVolumeChange);
      }
      $(document).keyup(this.bindExitFullScreen);
      this.$('.add-fullscreen').click(this.toggleFullScreen);
      if (!onTouchBasedDevice()) {
        return this.addToolTip();
      }
    };

    VideoPlayerAlpha.prototype.bindExitFullScreen = function(event) {
      if (this.el.hasClass('fullscreen') && event.keyCode === 27) {
        return this.toggleFullScreen(event);
      }
    };

    VideoPlayerAlpha.prototype.addToolTip = function() {
      return this.$('.add-fullscreen, .hide-subtitles').qtip({
        position: {
          my: 'top right',
          at: 'top center'
        }
      });
    };



    VideoPlayerAlpha.prototype.onPlaybackQualityChange = function(event, value) {
      var quality;
      quality = this.player.getPlaybackQuality();
      return this.qualityControl.onQualityChange(quality);
    };

    VideoPlayerAlpha.prototype.handlePlaybackQualityChange = function(event, value) {
      return this.player.setPlaybackQuality(value);
    };

    VideoPlayerAlpha.prototype.onUnstarted = function() {
      this.control.pause();
      if (this.video.show_captions === true) {
        return this.caption.pause();
      }
    };

    VideoPlayerAlpha.prototype.onPlay = function() {
      this.video.log('play_video');
      if (!this.player.interval) {
        this.player.interval = setInterval(this.update, 200);
      }
      if (this.video.show_captions === true) {
        this.caption.play();
      }
      this.control.play();
      return this.progressSlider.play();
    };

    VideoPlayerAlpha.prototype.onPause = function() {
      this.video.log('pause_video');
      clearInterval(this.player.interval);
      this.player.interval = null;
      if (this.video.show_captions === true) {
        this.caption.pause();
      }
      return this.control.pause();
    };

    VideoPlayerAlpha.prototype.onEnded = function() {
      this.control.pause();
      if (this.video.show_captions === true) {
        return this.caption.pause();
      }
    };

    VideoPlayerAlpha.prototype.onSeek = function(event, time) {
      this.player.seekTo(time, true);
      if (this.isPlaying()) {
        clearInterval(this.player.interval);
        this.player.interval = setInterval(this.update, 200);
      } else {
        this.currentTime = time;
      }
      return this.updatePlayTime(time);
    };

    VideoPlayerAlpha.prototype.onSpeedChange = function(event, newSpeed, updateCookie) {
      if (this.video.videoType === 'youtube') {
        this.currentTime = Time.convert(this.currentTime, parseFloat(this.currentSpeed()), newSpeed);
      }
      newSpeed = parseFloat(newSpeed).toFixed(2).replace(/\.00$/, '.0');
      this.video.setSpeed(newSpeed, updateCookie);
      if (this.video.videoType === 'youtube') {
        if (this.video.show_captions === true) {
          this.caption.currentSpeed = newSpeed;
        }
      }
      if (this.video.videoType === 'html5') {
        this.player.setPlaybackRate(newSpeed);
      } else if (this.video.videoType === 'youtube') {
        if (this.isPlaying()) {
          this.player.loadVideoById(this.video.youtubeId(), this.currentTime);
        } else {
          this.player.cueVideoById(this.video.youtubeId(), this.currentTime);
        }
      }
      if (this.video.videoType === 'youtube') {
        return this.updatePlayTime(this.currentTime);
      }
    };

    VideoPlayerAlpha.prototype.onVolumeChange = function(event, volume) {
      return this.player.setVolume(volume);
    };

    VideoPlayerAlpha.prototype.update = function() {
      if (this.currentTime = this.player.getCurrentTime()) {
        return this.updatePlayTime(this.currentTime);
      }
    };

    VideoPlayerAlpha.prototype.updatePlayTime = function(time) {
      var progress;
      progress = Time.format(time) + ' / ' + Time.format(this.duration());
      this.$(".vidtime").html(progress);
      if (this.video.show_captions === true) {
        this.caption.updatePlayTime(time);
      }
      return this.progressSlider.updatePlayTime(time, this.duration());
    };

    VideoPlayerAlpha.prototype.toggleFullScreen = function(event) {
      event.preventDefault();
      if (this.el.hasClass('fullscreen')) {
        this.$('.add-fullscreen').attr('title', 'Fill browser');
        this.el.removeClass('fullscreen');
      } else {
        this.el.addClass('fullscreen');
        this.$('.add-fullscreen').attr('title', 'Exit fill browser');
      }
      if (this.video.show_captions === true) {
        return this.caption.resize();
      }
    };

    VideoPlayerAlpha.prototype.play = function() {
      if (this.player.playVideo) {
        return this.player.playVideo();
      }
    };

    VideoPlayerAlpha.prototype.isPlaying = function() {
      return this.player.getPlayerState() === this.PlayerState.PLAYING;
    };

    VideoPlayerAlpha.prototype.pause = function() {
      if (this.player.pauseVideo) {
        return this.player.pauseVideo();
      }
    };

    VideoPlayerAlpha.prototype.duration = function() {
      var duration;
      duration = this.player.getDuration();
      if (isFinite(duration) === false) {
        duration = this.video.getDuration();
      }
      return duration;
    };

    VideoPlayerAlpha.prototype.currentSpeed = function() {
      return this.video.speed;
    };

    VideoPlayerAlpha.prototype.volume = function(value) {
      if (value != null) {
        return this.player.setVolume(value);
      } else {
        return this.player.getVolume();
      }
    };

    return VideoPlayerAlpha;

  })(SubviewAlpha);

}).call(this);

*/
