(function() {
  describe('VideoPlayerAlpha', function() {
    var playerVars, state, videoPlayer, player, videoControl, videoCaption, videoProgressSlider;

    function initialize() {
      loadFixtures('videoalpha_all.html');

      state = new VideoAlpha('#example');
      videoPlayer = state.videoPlayer;
      player = videoPlayer.player;
      videoControl = state.videoControl;
      videoCaption = state.videoCaption;
      videoProgressSlider = state.videoProgressSlider;
    }

    xdescribe('constructor', function() {
      beforeEach(function() {
        return $.fn.qtip.andCallFake(function() {
          return $(this).data('qtip', true);
        });
      });
      xdescribe('always', function() {
        beforeEach(function() {
          jasmine.stubVideoPlayerAlpha(this, [], false);
          $('.video').append($('<div class="add-fullscreen" /><div class="hide-subtitles" />'));
          return this.player = new VideoPlayerAlpha({
            video: this.video
          });
        });
        it('instanticate current time to zero', function() {
          return expect(this.player.currentTime).toEqual(0);
        });
        it('set the element', function() {
          return expect(this.player.el).toHaveId('video_id');
        });
        it('create video control', function() {
          expect(window.VideoControlAlpha.prototype.initialize).toHaveBeenCalled();
          expect(this.player.control).toBeDefined();
          return expect(this.player.control.el).toBe($('.video-controls', this.player.el));
        });
        it('create video caption', function() {
          expect(window.VideoCaptionAlpha.prototype.initialize).toHaveBeenCalled();
          expect(this.player.caption).toBeDefined();
          expect(this.player.caption.el).toBe(this.player.el);
          expect(this.player.caption.youtubeId).toEqual('normalSpeedYoutubeId');
          expect(this.player.caption.currentSpeed).toEqual('1.0');
          return expect(this.player.caption.captionAssetPath).toEqual('/static/subs/');
        });
        it('create video speed control', function() {
          expect(window.VideoSpeedControlAlpha.prototype.initialize).toHaveBeenCalled();
          expect(this.player.speedControl).toBeDefined();
          expect(this.player.speedControl.el).toBe($('.secondary-controls', this.player.el));
          expect(this.player.speedControl.speeds).toEqual(['0.75', '1.0']);
          return expect(this.player.speedControl.currentSpeed).toEqual('1.0');
        });
        it('create video progress slider', function() {
          expect(window.VideoSpeedControlAlpha.prototype.initialize).toHaveBeenCalled();
          expect(this.player.progressSlider).toBeDefined();
          return expect(this.player.progressSlider.el).toBe($('.slider', this.player.el));
        });
        it('bind to video control play event', function() {
          return expect($(this.player.control)).toHandleWith('play', this.player.play);
        });
        it('bind to video control pause event', function() {
          return expect($(this.player.control)).toHandleWith('pause', this.player.pause);
        });
        it('bind to video caption seek event', function() {
          return expect($(this.player.caption)).toHandleWith('caption_seek', this.player.onSeek);
        });
        it('bind to video speed control speedChange event', function() {
          return expect($(this.player.speedControl)).toHandleWith('speedChange', this.player.onSpeedChange);
        });
        it('bind to video progress slider seek event', function() {
          return expect($(this.player.progressSlider)).toHandleWith('slide_seek', this.player.onSeek);
        });
        it('bind to video volume control volumeChange event', function() {
          return expect($(this.player.volumeControl)).toHandleWith('volumeChange', this.player.onVolumeChange);
        });
        it('bind to key press', function() {
          return expect($(document.documentElement)).toHandleWith('keyup', this.player.bindExitFullScreen);
        });
        return it('bind to fullscreen switching button', function() {
          return expect($('.add-fullscreen')).toHandleWith('click', this.player.toggleFullScreen);
        });
      });
      it('create Youtube player', function() {
        jasmine.stubVideoPlayerAlpha(this, [], false);
        $('.video').append($('<div class="add-fullscreen" /><div class="hide-subtitles" />'));
        spyOn(YT, 'Player');
        this.player = new VideoPlayerAlpha({
          video: this.video
        });
        return expect(YT.Player).toHaveBeenCalledWith('id', {
          playerVars: playerVars,
          videoId: 'normalSpeedYoutubeId',
          events: {
            onReady: this.player.onReady,
            onStateChange: this.player.onStateChange,
            onPlaybackQualityChange: this.player.onPlaybackQualityChange
          }
        });
      });
      it('create HTML5 player', function() {
        jasmine.stubVideoPlayerAlpha(this, [], false, true);
        spyOn(HTML5Video, 'Player');
        $('.video').append($('<div class="add-fullscreen" /><div class="hide-subtitles" />'));
        this.player = new VideoPlayerAlpha({
          video: this.video
        });
        return expect(HTML5Video.Player).toHaveBeenCalledWith(this.video.el, {
          playerVars: playerVars,
          videoSources: this.video.html5Sources,
          events: {
            onReady: this.player.onReady,
            onStateChange: this.player.onStateChange
          }
        });
      });
      xdescribe('when not on a touch based device', function() {
        beforeEach(function() {
          jasmine.stubVideoPlayerAlpha(this, [], false);
          $('.video').append($('<div class="add-fullscreen" /><div class="hide-subtitles" />'));
          $('.add-fullscreen, .hide-subtitles').removeData('qtip');
          return this.player = new VideoPlayerAlpha({
            video: this.video
          });
        });
        it('add the tooltip to fullscreen and subtitle button', function() {
          expect($('.add-fullscreen')).toHaveData('qtip');
          return expect($('.hide-subtitles')).toHaveData('qtip');
        });
        return it('create video volume control', function() {
          expect(window.VideoVolumeControlAlpha.prototype.initialize).toHaveBeenCalled();
          expect(this.player.volumeControl).toBeDefined();
          return expect(this.player.volumeControl.el).toBe($('.secondary-controls', this.player.el));
        });
      });
      return xdescribe('when on a touch based device', function() {
        beforeEach(function() {
          jasmine.stubVideoPlayerAlpha(this, [], false);
          $('.video').append($('<div class="add-fullscreen" /><div class="hide-subtitles" />'));
          window.onTouchBasedDevice.andReturn(true);
          $('.add-fullscreen, .hide-subtitles').removeData('qtip');
          return this.player = new VideoPlayerAlpha({
            video: this.video
          });
        });
        it('does not add the tooltip to fullscreen and subtitle button', function() {
          expect($('.add-fullscreen')).not.toHaveData('qtip');
          return expect($('.hide-subtitles')).not.toHaveData('qtip');
        });
        return it('does not create video volume control', function() {
          expect(window.VideoVolumeControlAlpha.prototype.initialize).not.toHaveBeenCalled();
          return expect(this.player.volumeControl).not.toBeDefined();
        });
      });
    });
    xdescribe('onReady', function() {
      beforeEach(function() {
        jasmine.stubVideoPlayerAlpha(this, [], false);
        spyOn(this.video, 'log');
        $('.video').append($('<div class="add-fullscreen" /><div class="hide-subtitles" />'));
        this.video.embed();
        this.player = this.video.player;
        spyOnEvent(this.player, 'ready');
        spyOnEvent(this.player, 'updatePlayTime');
        return this.player.onReady();
      });
      it('log the load_video event', function() {
        return expect(this.video.log).toHaveBeenCalledWith('load_video');
      });
      xdescribe('when not on a touch based device', function() {
        beforeEach(function() {
          spyOn(this.player, 'play');
          return this.player.onReady();
        });
        return it('autoplay the first video', function() {
          return expect(this.player.play).toHaveBeenCalled();
        });
      });
      return xdescribe('when on a touch based device', function() {
        beforeEach(function() {
          window.onTouchBasedDevice.andReturn(true);
          spyOn(this.player, 'play');
          return this.player.onReady();
        });
        return it('does not autoplay the first video', function() {
          return expect(this.player.play).not.toHaveBeenCalled();
        });
      });
    });
    xdescribe('onStateChange', function() {
      beforeEach(function() {
        jasmine.stubVideoPlayerAlpha(this, [], false);
        return $('.video').append($('<div class="add-fullscreen" /><div class="hide-subtitles" />'));
      });
      xdescribe('when the video is unstarted', function() {
        beforeEach(function() {
          this.player = new VideoPlayerAlpha({
            video: this.video
          });
          spyOn(this.player.control, 'pause');
          this.player.caption.pause = jasmine.createSpy('VideoCaptionAlpha.pause');
          return this.player.onStateChange({
            data: YT.PlayerState.UNSTARTED
          });
        });
        it('pause the video control', function() {
          return expect(this.player.control.pause).toHaveBeenCalled();
        });
        return it('pause the video caption', function() {
          return expect(this.player.caption.pause).toHaveBeenCalled();
        });
      });
      xdescribe('when the video is playing', function() {
        beforeEach(function() {
          this.anotherPlayer = jasmine.createSpyObj('AnotherPlayer', ['onPause']);
          window.OldVideoPlayerAlpha = this.anotherPlayer;
          this.player = new VideoPlayerAlpha({
            video: this.video
          });
          spyOn(this.video, 'log');
          spyOn(window, 'setInterval').andReturn(100);
          spyOn(this.player.control, 'play');
          this.player.caption.play = jasmine.createSpy('VideoCaptionAlpha.play');
          this.player.progressSlider.play = jasmine.createSpy('VideoProgressSliderAlpha.play');
          this.player.player.getVideoEmbedCode.andReturn('embedCode');
          return this.player.onStateChange({
            data: YT.PlayerState.PLAYING
          });
        });
        it('log the play_video event', function() {
          return expect(this.video.log).toHaveBeenCalledWith('play_video', {
            currentTime: 0
          });
        });
        it('pause other video player', function() {
          return expect(this.anotherPlayer.onPause).toHaveBeenCalled();
        });
        it('set current video player as active player', function() {
          return expect(window.OldVideoPlayerAlpha).toEqual(this.player);
        });
        it('set update interval', function() {
          expect(window.setInterval).toHaveBeenCalledWith(this.player.update, 200);
          return expect(this.player.player.interval).toEqual(100);
        });
        it('play the video control', function() {
          return expect(this.player.control.play).toHaveBeenCalled();
        });
        it('play the video caption', function() {
          return expect(this.player.caption.play).toHaveBeenCalled();
        });
        return it('play the video progress slider', function() {
          return expect(this.player.progressSlider.play).toHaveBeenCalled();
        });
      });
      xdescribe('when the video is paused', function() {
        beforeEach(function() {
          this.player = new VideoPlayerAlpha({
            video: this.video
          });
          spyOn(this.video, 'log');
          spyOn(window, 'clearInterval');
          spyOn(this.player.control, 'pause');
          this.player.caption.pause = jasmine.createSpy('VideoCaptionAlpha.pause');
          this.player.player.interval = 100;
          this.player.player.getVideoEmbedCode.andReturn('embedCode');
          return this.player.onStateChange({
            data: YT.PlayerState.PAUSED
          });
        });
        it('log the pause_video event', function() {
          return expect(this.video.log).toHaveBeenCalledWith('pause_video', {
            currentTime: 0
          });
        });
        it('clear update interval', function() {
          expect(window.clearInterval).toHaveBeenCalledWith(100);
          return expect(this.player.player.interval).toBeNull();
        });
        it('pause the video control', function() {
          return expect(this.player.control.pause).toHaveBeenCalled();
        });
        return it('pause the video caption', function() {
          return expect(this.player.caption.pause).toHaveBeenCalled();
        });
      });
      return xdescribe('when the video is ended', function() {
        beforeEach(function() {
          this.player = new VideoPlayerAlpha({
            video: this.video
          });
          spyOn(this.player.control, 'pause');
          this.player.caption.pause = jasmine.createSpy('VideoCaptionAlpha.pause');
          return this.player.onStateChange({
            data: YT.PlayerState.ENDED
          });
        });
        it('pause the video control', function() {
          return expect(this.player.control.pause).toHaveBeenCalled();
        });
        return it('pause the video caption', function() {
          return expect(this.player.caption.pause).toHaveBeenCalled();
        });
      });
    });

    describe('onSeek', function() {
      beforeEach(function() {
        spyOn(window, 'clearInterval').andCallThrough();

        initialize();

        videoPlayer.updateInterval = 100;

        spyOn(videoPlayer, 'updatePlayTime').andCallThrough();
        spyOn(videoPlayer, 'log').andCallThrough();
        spyOn(videoPlayer.player, 'seekTo').andCallThrough();
      });

      it('Slider event causes log update', function () {
        videoProgressSlider.onSlide(jQuery.Event('slide'), {value: 60});

        expect(videoPlayer.log).toHaveBeenCalledWith(
          'seek_video',
          {
            old_time: 0,
            new_time: 60,
            type: 'onSlideSeek'
          }
        );
      });

      it('seek the player', function() {
        videoProgressSlider.onSlide(jQuery.Event('slide'), {value: 60});

        expect(videoPlayer.player.seekTo).toHaveBeenCalledWith(60, true);
      });

      it('call updatePlayTime on player', function() {
        videoProgressSlider.onSlide(jQuery.Event('slide'), {value: 60});

        expect(videoPlayer.updatePlayTime).toHaveBeenCalledWith(60);
      });

      it('when the player is playing: reset the update interval', function() {
        videoProgressSlider.onSlide(jQuery.Event('slide'), {value: 60});

        expect(window.clearInterval).toHaveBeenCalledWith(100);
      });

      it('when the player is not playing: set the current time', function() {
        videoProgressSlider.onSlide(jQuery.Event('slide'), {value: 60});
        videoPlayer.pause();

        expect(videoPlayer.currentTime).toEqual(60);
      });
    });

    describe('onSpeedChange', function() {
      beforeEach(function() {
        initialize();

        videoPlayer.currentTime = 60;

        spyOn(videoPlayer, 'updatePlayTime').andCallThrough();
        spyOn(state, 'setSpeed').andCallThrough();
        spyOn(videoPlayer, 'log').andCallThrough();
        spyOn(videoPlayer.player, 'setPlaybackRate').andCallThrough();
      });

      describe('always', function() {
        beforeEach(function() {
          videoPlayer.onSpeedChange('0.75', false);
        });

        it('check if speed_change_video is logged', function() {
          expect(videoPlayer.log).toHaveBeenCalledWith('speed_change_video', {
            current_time: videoPlayer.currentTime,
            old_speed: '1.0',
            new_speed: '0.75'
          });
        });

        it('convert the current time to the new speed', function() {
          expect(videoPlayer.currentTime).toEqual(60);
        });

        it('set video speed to the new speed', function() {
          expect(state.setSpeed).toHaveBeenCalledWith('0.75', false);
        });

        // Not relevant any more.
        //
        // it('tell video caption that the speed has changed', function() {
        //   expect(this.player.caption.currentSpeed).toEqual('0.75');
        // });
      });

      describe('when the video is playing', function() {
        beforeEach(function() {
          videoPlayer.play();

          videoPlayer.onSpeedChange('0.75', false);
        });

        it('trigger updatePlayTime event', function() {
          expect(videoPlayer.player.setPlaybackRate).toHaveBeenCalledWith('0.75');
        });
      });

      describe('when the video is not playing', function() {
        beforeEach(function() {
          videoPlayer.pause();

          videoPlayer.onSpeedChange('0.75', false);
        });

        it('trigger updatePlayTime event', function() {
          expect(videoPlayer.player.setPlaybackRate).toHaveBeenCalledWith('0.75');
        });
      });
    });

    describe('onVolumeChange', function() {
      beforeEach(function() {
        initialize();

        spyOn(videoPlayer.player, 'setVolume');
        videoPlayer.onVolumeChange(60);
      });

      it('set the volume on player', function() {
        expect(videoPlayer.player.setVolume).toHaveBeenCalledWith(60);
      });
    });

    describe('update', function() {
      beforeEach(function() {
        initialize();

        spyOn(videoPlayer, 'updatePlayTime').andCallThrough();
      });

      describe('when the current time is unavailable from the player', function() {
        beforeEach(function() {
          videoPlayer.player.getCurrentTime = function () {
            return NaN;
          }
          videoPlayer.update();
        });

        it('does not trigger updatePlayTime event', function() {
          expect(videoPlayer.updatePlayTime).not.toHaveBeenCalled();
        });
      });

      describe('when the current time is available from the player', function() {
        beforeEach(function() {
          videoPlayer.player.getCurrentTime = function () {
            return 60;
          }
          videoPlayer.update();
        });

        it('trigger updatePlayTime event', function() {
          expect(videoPlayer.updatePlayTime).toHaveBeenCalledWith(60);
        });
      });
    });

    describe('updatePlayTime', function() {
      beforeEach(function() {
        initialize();

        spyOn(videoCaption, 'updatePlayTime').andCallThrough();
        spyOn(videoProgressSlider, 'updatePlayTime').andCallThrough();
      });

      it('update the video playback time', function() {
        var duration = 0;

        waitsFor(function () {
          duration = videoPlayer.duration();

          if (duration > 0) {
            return true;
          }

          return false;
        }, 'Video is fully loaded.', 1000);

        runs(function () {
          videoPlayer.updatePlayTime(60);

          expect($('.vidtime')).toHaveHtml('1:00 / 1:01');
        });
      });

      it('update the playback time on caption', function() {
        var duration = 0;

        waitsFor(function () {
          duration = videoPlayer.duration();

          if (duration > 0) {
            return true;
          }

          return false;
        }, 'Video is fully loaded.', 1000);

        runs(function () {
          videoPlayer.updatePlayTime(60);

          expect(videoCaption.updatePlayTime).toHaveBeenCalledWith(60);
        });
      });

      it('update the playback time on progress slider', function() {
        var duration = 0;

        waitsFor(function () {
          duration = videoPlayer.duration();

          if (duration > 0) {
            return true;
          }

          return false;
        }, 'Video is fully loaded.', 1000);

        runs(function () {
          videoPlayer.updatePlayTime(60);

          expect(videoProgressSlider.updatePlayTime).toHaveBeenCalledWith({
            time: 60,
            duration: duration
          });
        });
      });
    });

    describe('toggleFullScreen', function() {
      describe('when the video player is not full screen', function() {
        beforeEach(function() {
          initialize();
          spyOn(videoCaption, 'resize').andCallThrough();
          videoControl.toggleFullScreen(jQuery.Event("click"));
        });

        it('replace the full screen button tooltip', function() {
          expect($('.add-fullscreen')).toHaveAttr('title', 'Exit fullscreen');
        });

        it('add the fullscreen class', function() {
          expect(state.el).toHaveClass('fullscreen');
        });

        it('tell VideoCaption to resize', function() {
          expect(videoCaption.resize).toHaveBeenCalled();
        });
      });

      describe('when the video player already full screen', function() {
        beforeEach(function() {
          initialize();
          spyOn(videoCaption, 'resize').andCallThrough();

          state.el.addClass('fullscreen');
          videoControl.fullScreenState = true;
          isFullScreen = true;
          videoControl.fullScreenEl.attr('title', 'Exit-fullscreen');

          videoControl.toggleFullScreen(jQuery.Event("click"));
        });

        it('replace the full screen button tooltip', function() {
          expect($('.add-fullscreen')).toHaveAttr('title', 'Fullscreen');
        });

        it('remove the fullscreen class', function() {
          expect(state.el).not.toHaveClass('fullscreen');
        });

        it('tell VideoCaption to resize', function() {
          expect(videoCaption.resize).toHaveBeenCalled();
        });
      });
    });

    describe('play', function() {
      beforeEach(function() {
        initialize();
        spyOn(player, 'playVideo').andCallThrough();
      });

      describe('when the player is not ready', function() {
        beforeEach(function() {
          player.playVideo = void 0;
          videoPlayer.play();
        });
        it('does nothing', function() {
          expect(player.playVideo).toBeUndefined();
        });
      });

      describe('when the player is ready', function() {
        beforeEach(function() {
          player.playVideo.andReturn(true);
          videoPlayer.play();
        });

        it('delegate to the player', function() {
          expect(player.playVideo).toHaveBeenCalled();
        });
      });
    });

    describe('isPlaying', function() {
      beforeEach(function() {
        initialize();
        spyOn(player, 'getPlayerState').andCallThrough();
      });

      describe('when the video is playing', function() {
        beforeEach(function() {
          player.getPlayerState.andReturn(YT.PlayerState.PLAYING);
        });

        it('return true', function() {
          expect(videoPlayer.isPlaying()).toBeTruthy();
        });
      });

      describe('when the video is not playing', function() {
        beforeEach(function() {
          player.getPlayerState.andReturn(YT.PlayerState.PAUSED);
        });

        it('return false', function() {
          expect(videoPlayer.isPlaying()).toBeFalsy();
        });
      });
    });

    describe('pause', function() {
      beforeEach(function() {
        initialize();
        spyOn(player, 'pauseVideo').andCallThrough();
        videoPlayer.pause();
      });

      it('delegate to the player', function() {
        expect(player.pauseVideo).toHaveBeenCalled();
      });
    });

    describe('duration', function() {
      beforeEach(function() {
        initialize();
        spyOn(player, 'getDuration').andCallThrough();
        videoPlayer.duration();
      });

      it('delegate to the player', function() {
        expect(player.getDuration).toHaveBeenCalled();
      });
    });

    describe('playback rate', function() {
      beforeEach(function() {
        initialize();
        player.setPlaybackRate(1.5);
      });

      it('set the player playback rate', function() {
        expect(player.video.playbackRate).toEqual(1.5);
      });
    });

    describe('volume', function() {
      beforeEach(function() {
        initialize();
        spyOn(player, 'getVolume').andCallThrough();
      });

      it('set the player volume', function() {
        player.setVolume(60);
        expect(player.getVolume()).toEqual(0.6);
      });
    });
  });

}).call(this);
