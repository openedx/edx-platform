(function() {

  describe('VideoPlayer', function() {
    beforeEach(function() {
      return jasmine.stubVideoPlayer(this);
    });
    afterEach(function() {
      return YT.Player = void 0;
    });
    describe('constructor', function() {
      beforeEach(function() {
        spyOn(window, 'VideoControl');
        spyOn(YT, 'Player');
        $.fn.qtip.andCallFake(function() {
          return $(this).data('qtip', true);
        });
        $('.video').append($('<div class="hide-subtitles" />'));
        return this.player = new VideoPlayer(this.video);
      });
      it('instanticate current time to zero', function() {
        return expect(this.player.currentTime).toEqual(0);
      });
      it('set the element', function() {
        return expect(this.player.element).toBe('#video_example');
      });
      it('create video control', function() {
        return expect(window.VideoControl).toHaveBeenCalledWith(this.player);
      });
      it('create video caption', function() {
        return expect(window.VideoCaption).toHaveBeenCalledWith(this.player, 'def456');
      });
      it('create video speed control', function() {
        return expect(window.VideoSpeedControl).toHaveBeenCalledWith(this.player, ['0.75', '1.0']);
      });
      it('create video progress slider', function() {
        return expect(window.VideoProgressSlider).toHaveBeenCalledWith(this.player);
      });
      it('create Youtube player', function() {
        return expect(YT.Player).toHaveBeenCalledWith('example', {
          playerVars: {
            controls: 0,
            wmode: 'transparent',
            rel: 0,
            showinfo: 0,
            enablejsapi: 1
          },
          videoId: 'def456',
          events: {
            onReady: this.player.onReady,
            onStateChange: this.player.onStateChange
          }
        });
      });
      it('bind to seek event', function() {
        return expect($(this.player)).toHandleWith('seek', this.player.onSeek);
      });
      it('bind to updatePlayTime event', function() {
        return expect($(this.player)).toHandleWith('updatePlayTime', this.player.onUpdatePlayTime);
      });
      it('bidn to speedChange event', function() {
        return expect($(this.player)).toHandleWith('speedChange', this.player.onSpeedChange);
      });
      it('bind to play event', function() {
        return expect($(this.player)).toHandleWith('play', this.player.onPlay);
      });
      it('bind to paused event', function() {
        return expect($(this.player)).toHandleWith('pause', this.player.onPause);
      });
      it('bind to ended event', function() {
        return expect($(this.player)).toHandleWith('ended', this.player.onPause);
      });
      it('bind to key press', function() {
        return expect($(document)).toHandleWith('keyup', this.player.bindExitFullScreen);
      });
      it('bind to fullscreen switching button', function() {
        return expect($('.add-fullscreen')).toHandleWith('click', this.player.toggleFullScreen);
      });
      return describe('when not on a touch based device', function() {
        return it('add the tooltip to fullscreen and subtitle button', function() {
          expect($('.add-fullscreen')).toHaveData('qtip');
          return expect($('.hide-subtitles')).toHaveData('qtip');
        });
      });
    });
    describe('onReady', function() {
      beforeEach(function() {
        this.video.embed();
        this.player = this.video.player;
        spyOnEvent(this.player, 'ready');
        spyOnEvent(this.player, 'updatePlayTime');
        return this.player.onReady();
      });
      it('reset the progress to zero', function() {
        return expect('updatePlayTime').toHaveBeenTriggeredOn(this.player);
      });
      it('trigger ready event on the player', function() {
        return expect('ready').toHaveBeenTriggeredOn(this.player);
      });
      describe('when not on a touch based device', function() {
        beforeEach(function() {
          window.onTouchBasedDevice = function() {
            return false;
          };
          spyOn(this.player, 'play');
          return this.player.onReady();
        });
        return it('autoplay the first video', function() {
          return expect(this.player.play).toHaveBeenCalled();
        });
      });
      return describe('when on a touch based device', function() {
        beforeEach(function() {
          window.onTouchBasedDevice = function() {
            return true;
          };
          spyOn(this.player, 'play');
          return this.player.onReady();
        });
        return it('does not autoplay the first video', function() {
          return expect(this.player.play).not.toHaveBeenCalled();
        });
      });
    });
    describe('onStateChange', function() {
      beforeEach(function() {
        return this.player = new VideoPlayer(this.video);
      });
      describe('when the video is playing', function() {
        beforeEach(function() {
          spyOnEvent(this.player, 'play');
          return this.player.onStateChange({
            data: YT.PlayerState.PLAYING
          });
        });
        return it('trigger play event', function() {
          return expect('play').toHaveBeenTriggeredOn(this.player);
        });
      });
      describe('when the video is paused', function() {
        beforeEach(function() {
          spyOnEvent(this.player, 'pause');
          return this.player.onStateChange({
            data: YT.PlayerState.PAUSED
          });
        });
        return it('trigger pause event', function() {
          return expect('pause').toHaveBeenTriggeredOn(this.player);
        });
      });
      return describe('when the video is ended', function() {
        beforeEach(function() {
          spyOnEvent(this.player, 'ended');
          return this.player.onStateChange({
            data: YT.PlayerState.ENDED
          });
        });
        return it('trigger ended event', function() {
          return expect('ended').toHaveBeenTriggeredOn(this.player);
        });
      });
    });
    describe('onPlay', function() {
      beforeEach(function() {
        this.player = new VideoPlayer(this.video);
        this.anotherPlayer = jasmine.createSpyObj('AnotherPlayer', ['pauseVideo']);
        window.player = this.anotherPlayer;
        spyOn(Logger, 'log');
        spyOn(window, 'setInterval').andReturn(100);
        this.player.player.getVideoEmbedCode.andReturn('embedCode');
        return this.player.onPlay();
      });
      it('log the play_video event', function() {
        return expect(Logger.log).toHaveBeenCalledWith('play_video', {
          id: this.player.currentTime,
          code: 'embedCode'
        });
      });
      it('pause other video player', function() {
        return expect(this.anotherPlayer.pauseVideo).toHaveBeenCalled();
      });
      it('set current video player as active player', function() {
        return expect(window.player).toEqual(this.player.player);
      });
      return it('set update interval', function() {
        expect(window.setInterval).toHaveBeenCalledWith(this.player.update, 200);
        return expect(this.player.player.interval).toEqual(100);
      });
    });
    describe('onPause', function() {
      beforeEach(function() {
        this.player = new VideoPlayer(this.video);
        window.player = this.player.player;
        spyOn(Logger, 'log');
        spyOn(window, 'clearInterval');
        this.player.player.interval = 100;
        this.player.player.getVideoEmbedCode.andReturn('embedCode');
        return this.player.onPause();
      });
      it('log the pause_video event', function() {
        return expect(Logger.log).toHaveBeenCalledWith('pause_video', {
          id: this.player.currentTime,
          code: 'embedCode'
        });
      });
      it('set current video player as inactive', function() {
        return expect(window.player).toBeNull();
      });
      return it('clear update interval', function() {
        expect(window.clearInterval).toHaveBeenCalledWith(100);
        return expect(this.player.player.interval).toBeNull();
      });
    });
    describe('onSeek', function() {
      beforeEach(function() {
        this.player = new VideoPlayer(this.video);
        spyOn(window, 'clearInterval');
        this.player.player.interval = 100;
        return this.player.onSeek({}, 60);
      });
      it('seek the player', function() {
        return expect(this.player.player.seekTo).toHaveBeenCalledWith(60, true);
      });
      describe('when the player is playing', function() {
        beforeEach(function() {
          this.player.player.getPlayerState.andReturn(YT.PlayerState.PLAYING);
          return this.player.onSeek({}, 60);
        });
        return it('reset the update interval', function() {
          return expect(window.clearInterval).toHaveBeenCalledWith(100);
        });
      });
      return describe('when the player is not playing', function() {
        beforeEach(function() {
          this.player.player.getPlayerState.andReturn(YT.PlayerState.PAUSED);
          spyOnEvent(this.player, 'updatePlayTime');
          return this.player.onSeek({}, 60);
        });
        it('set the current time', function() {
          return expect(this.player.currentTime).toEqual(60);
        });
        return it('trigger updatePlayTime event', function() {
          return expect('updatePlayTime').toHaveBeenTriggeredOn(this.player);
        });
      });
    });
    describe('onSpeedChange', function() {
      beforeEach(function() {
        this.player = new VideoPlayer(this.video);
        this.player.currentTime = 60;
        return spyOn(this.video, 'setSpeed').andCallThrough();
      });
      describe('always', function() {
        beforeEach(function() {
          return this.player.onSpeedChange({}, '0.75');
        });
        it('convert the current time to the new speed', function() {
          return expect(this.player.currentTime).toEqual('80.000');
        });
        return it('set video speed to the new speed', function() {
          return expect(this.video.setSpeed).toHaveBeenCalledWith('0.75');
        });
      });
      describe('when the video is playing', function() {
        beforeEach(function() {
          this.player.player.getPlayerState.andReturn(YT.PlayerState.PLAYING);
          spyOnEvent(this.player, 'updatePlayTime');
          return this.player.onSpeedChange({}, '0.75');
        });
        it('load the video', function() {
          return expect(this.player.player.loadVideoById).toHaveBeenCalledWith('abc123', '80.000');
        });
        return it('trigger updatePlayTime event', function() {
          return expect('updatePlayTime').toHaveBeenTriggeredOn(this.player);
        });
      });
      return describe('when the video is not playing', function() {
        beforeEach(function() {
          this.player.player.getPlayerState.andReturn(YT.PlayerState.PAUSED);
          spyOnEvent(this.player, 'updatePlayTime');
          return this.player.onSpeedChange({}, '0.75');
        });
        it('cue the video', function() {
          return expect(this.player.player.cueVideoById).toHaveBeenCalledWith('abc123', '80.000');
        });
        return it('trigger updatePlayTime event', function() {
          return expect('updatePlayTime').toHaveBeenTriggeredOn(this.player);
        });
      });
    });
    describe('update', function() {
      beforeEach(function() {
        this.player = new VideoPlayer(this.video);
        return spyOnEvent(this.player, 'updatePlayTime');
      });
      describe('when the current time is unavailable from the player', function() {
        beforeEach(function() {
          this.player.player.getCurrentTime.andReturn(void 0);
          return this.player.update();
        });
        return it('does not trigger updatePlayTime event', function() {
          return expect('updatePlayTime').not.toHaveBeenTriggeredOn(this.player);
        });
      });
      return describe('when the current time is available from the player', function() {
        beforeEach(function() {
          this.player.player.getCurrentTime.andReturn(60);
          return this.player.update();
        });
        return it('trigger updatePlayTime event', function() {
          return expect('updatePlayTime').toHaveBeenTriggeredOn(this.player);
        });
      });
    });
    describe('onUpdatePlaytime', function() {
      beforeEach(function() {
        this.player = new VideoPlayer(this.video);
        spyOn(this.video, 'getDuration').andReturn(1800);
        return this.player.onUpdatePlayTime({}, 60);
      });
      return it('update the video playback time', function() {
        return expect($('.vidtime')).toHaveHtml('1:00 / 30:00');
      });
    });
    describe('toggleFullScreen', function() {
      beforeEach(function() {
        return this.player = new VideoPlayer(this.video);
      });
      describe('when the video player is not full screen', function() {
        beforeEach(function() {
          this.player.element.removeClass('fullscreen');
          spyOnEvent(this.player, 'resize');
          return this.player.toggleFullScreen(jQuery.Event("click"));
        });
        it('replace the full screen button tooltip', function() {
          return expect($('.add-fullscreen')).toHaveAttr('title', 'Exit fill browser');
        });
        it('add a new exit from fullscreen button', function() {
          return expect(this.player.element).toContain('a.exit');
        });
        it('add the fullscreen class', function() {
          return expect(this.player.element).toHaveClass('fullscreen');
        });
        return it('trigger resize event', function() {
          return expect('resize').toHaveBeenTriggeredOn(this.player);
        });
      });
      return describe('when the video player already full screen', function() {
        beforeEach(function() {
          this.player.element.addClass('fullscreen');
          spyOnEvent(this.player, 'resize');
          return this.player.toggleFullScreen(jQuery.Event("click"));
        });
        it('replace the full screen button tooltip', function() {
          return expect($('.add-fullscreen')).toHaveAttr('title', 'Fill browser');
        });
        it('remove exit full screen button', function() {
          return expect(this.player.element).not.toContain('a.exit');
        });
        it('remove the fullscreen class', function() {
          return expect(this.player.element).not.toHaveClass('fullscreen');
        });
        return it('trigger resize event', function() {
          return expect('resize').toHaveBeenTriggeredOn(this.player);
        });
      });
    });
    describe('play', function() {
      beforeEach(function() {
        return this.player = new VideoPlayer(this.video);
      });
      describe('when the player is not ready', function() {
        beforeEach(function() {
          this.player.player.playVideo = void 0;
          return this.player.play();
        });
        return it('does nothing', function() {
          return expect(this.player.player.playVideo).toBeUndefined();
        });
      });
      return describe('when the player is ready', function() {
        beforeEach(function() {
          this.player.player.playVideo.andReturn(true);
          return this.player.play();
        });
        return it('delegate to the Youtube player', function() {
          return expect(this.player.player.playVideo).toHaveBeenCalled();
        });
      });
    });
    describe('isPlaying', function() {
      beforeEach(function() {
        return this.player = new VideoPlayer(this.video);
      });
      describe('when the video is playing', function() {
        beforeEach(function() {
          return this.player.player.getPlayerState.andReturn(YT.PlayerState.PLAYING);
        });
        return it('return true', function() {
          return expect(this.player.isPlaying()).toBeTruthy();
        });
      });
      return describe('when the video is not playing', function() {
        beforeEach(function() {
          return this.player.player.getPlayerState.andReturn(YT.PlayerState.PAUSED);
        });
        return it('return false', function() {
          return expect(this.player.isPlaying()).toBeFalsy();
        });
      });
    });
    describe('pause', function() {
      beforeEach(function() {
        this.player = new VideoPlayer(this.video);
        return this.player.pause();
      });
      return it('delegate to the Youtube player', function() {
        return expect(this.player.player.pauseVideo).toHaveBeenCalled();
      });
    });
    describe('duration', function() {
      beforeEach(function() {
        this.player = new VideoPlayer(this.video);
        spyOn(this.video, 'getDuration');
        return this.player.duration();
      });
      return it('delegate to the video', function() {
        return expect(this.video.getDuration).toHaveBeenCalled();
      });
    });
    return describe('currentSpeed', function() {
      beforeEach(function() {
        this.player = new VideoPlayer(this.video);
        return this.video.speed = '3.0';
      });
      return it('delegate to the video', function() {
        return expect(this.player.currentSpeed()).toEqual('3.0');
      });
    });
  });

}).call(this);
