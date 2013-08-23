(function() {
  describe('VideoPlayer', function() {
    var state, videoPlayer, player, videoControl, videoCaption, videoProgressSlider, videoSpeedControl, videoVolumeControl, oldOTBD;

    function initialize(fixture) {
      if (typeof fixture === 'undefined') {
        loadFixtures('video_all.html');
      } else {
        loadFixtures(fixture);
      }

      state = new Video('#example');
      videoPlayer = state.videoPlayer;
      player = videoPlayer.player;
      videoControl = state.videoControl;
      videoCaption = state.videoCaption;
      videoProgressSlider = state.videoProgressSlider;
      videoSpeedControl = state.videoSpeedControl;
      videoVolumeControl = state.videoVolumeControl;
    }

    function initializeYouTube() {
        initialize('video.html');
    }

    beforeEach(function () {
        oldOTBD = window.onTouchBasedDevice;
        window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn(false);
    });

    afterEach(function() {
        $('source').remove();
        window.onTouchBasedDevice = oldOTBD;
    });

    describe('constructor', function() {
      describe('always', function() {
        beforeEach(function() {
          initialize();
        });

        it('instanticate current time to zero', function() {
          expect(videoPlayer.currentTime).toEqual(0);
        });

        it('set the element', function() {
          expect(state.el).toHaveId('video_id');
        });

        it('create video control', function() {
          expect(videoControl).toBeDefined();
          expect(videoControl.el).toHaveClass('video-controls');
        });

        it('create video caption', function() {
          expect(videoCaption).toBeDefined();
          expect(state.youtubeId()).toEqual('Z5KLxerq05Y');
          expect(state.speed).toEqual('1.0');
          expect(state.config.caption_asset_path).toEqual('/static/subs/');
        });

        it('create video speed control', function() {
          expect(videoSpeedControl).toBeDefined();
          expect(videoSpeedControl.el).toHaveClass('speeds');
          expect(videoSpeedControl.speeds).toEqual([ '0.75', '1.0', '1.25', '1.50' ]);
          expect(state.speed).toEqual('1.0');
        });

        it('create video progress slider', function() {
          expect(videoProgressSlider).toBeDefined();
          expect(videoProgressSlider.el).toHaveClass('slider');
        });

        // All the toHandleWith() expect tests are not necessary for this version of Video.
        // jQuery event system is not used to trigger and invoke methods. This is an artifact from
        // previous version of Video.
      });

      it('create Youtube player', function() {
        var oldYT = window.YT;

        jasmine.stubRequests();

        window.YT = {
            Player: function () { },
            PlayerState: oldYT.PlayerState
        };

        spyOn(window.YT, 'Player');

        initializeYouTube();

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
          events: {
            onReady: videoPlayer.onReady,
            onStateChange: videoPlayer.onStateChange,
            onPlaybackQualityChange: videoPlayer.onPlaybackQualityChange
          }
        });

        window.YT = oldYT;
      });

      // We can't test the invocation of HTML5Video because it is not available
      // globally. It is defined within the scope of Require JS.

      describe('when not on a touch based device', function() {
        beforeEach(function() {
          window.onTouchBasedDevice.andReturn(true);
          initialize();
        });

        it('create video volume control', function() {
          expect(videoVolumeControl).toBeDefined();
          expect(videoVolumeControl.el).toHaveClass('volume');
        });
      });

      describe('when on a touch based device', function() {
        var oldOTBD;

        beforeEach(function() {
          initialize();
        });

        it('controls are in paused state', function() {
          expect(videoControl.isPlaying).toBe(false);
        });
      });
    });

    describe('onReady', function() {
      beforeEach(function() {
        initialize();

        spyOn(videoPlayer, 'log').andCallThrough();
        spyOn(videoPlayer, 'play').andCallThrough();
        videoPlayer.onReady();
      });

      it('log the load_video event', function() {
        expect(videoPlayer.log).toHaveBeenCalledWith('load_video');
      });

      it('autoplay the first video', function() {
        expect(videoPlayer.play).not.toHaveBeenCalled();
      });
    });

    describe('onStateChange', function() {
      describe('when the video is unstarted', function() {
        beforeEach(function() {
          initialize();

          spyOn(videoControl, 'pause').andCallThrough();
          spyOn(videoCaption, 'pause').andCallThrough();

          videoPlayer.onStateChange({
            data: YT.PlayerState.PAUSED
          });
        });

        it('pause the video control', function() {
          expect(videoControl.pause).toHaveBeenCalled();
        });

        it('pause the video caption', function() {
          expect(videoCaption.pause).toHaveBeenCalled();
        });
      });

      describe('when the video is playing', function() {
        var oldState;

        beforeEach(function() {
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

        it('log the play_video event', function() {
          expect(videoPlayer.log).toHaveBeenCalledWith('play_video', {
            currentTime: 0
          });
        });

        it('pause other video player', function() {
          expect(oldState.videoPlayer.onPause).toHaveBeenCalled();
        });

        it('set update interval', function() {
          expect(window.setInterval).toHaveBeenCalledWith(videoPlayer.update, 200);
          expect(videoPlayer.updateInterval).toEqual(100);
        });

        it('play the video control', function() {
          expect(videoControl.play).toHaveBeenCalled();
        });

        it('play the video caption', function() {
          expect(videoCaption.play).toHaveBeenCalled();
        });
      });

      describe('when the video is paused', function() {
        var currentUpdateIntrval;

        beforeEach(function() {
          initialize();

          spyOn(videoPlayer, 'log').andCallThrough();
          spyOn(window, 'clearInterval').andCallThrough();
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

        it('log the pause_video event', function() {
          expect(videoPlayer.log).toHaveBeenCalledWith('pause_video', {
            currentTime: 0
          });
        });

        it('clear update interval', function() {
          expect(window.clearInterval).toHaveBeenCalledWith(currentUpdateIntrval);
          expect(videoPlayer.updateInterval).toBeUndefined();
        });

        it('pause the video control', function() {
          expect(videoControl.pause).toHaveBeenCalled();
        });

        it('pause the video caption', function() {
          expect(videoCaption.pause).toHaveBeenCalled();
        });
      });

      describe('when the video is ended', function() {
        beforeEach(function() {
          initialize();

          spyOn(videoControl, 'pause').andCallThrough();
          spyOn(videoCaption, 'pause').andCallThrough();

          videoPlayer.onStateChange({
            data: YT.PlayerState.ENDED
          });
        });

        it('pause the video control', function() {
          expect(videoControl.pause).toHaveBeenCalled();
        });

        it('pause the video caption', function() {
          expect(videoCaption.pause).toHaveBeenCalled();
        });
      });
    });

    describe('onSeek', function() {
      beforeEach(function() {
        spyOn(window, 'clearInterval').andCallThrough();

        initialize();

        videoPlayer.updateInterval = 100;

        spyOn(videoPlayer, 'updatePlayTime');
        spyOn(videoPlayer, 'log');
        spyOn(videoPlayer.player, 'seekTo');
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

        // Not relevant any more:
        //
        //     expect( "tell video caption that the speed has changed" ) ...
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
          };
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
          };
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
          var htmlStr;

          videoPlayer.updatePlayTime(60);

          htmlStr = $('.vidtime').html();

          // We resort to this trickery because Firefox and Chrome
          // round the total time a bit differently.
          if (htmlStr.match('1:00 / 1:01') || htmlStr.match('1:00 / 1:00')) {
            expect(true).toBe(true);
          } else {
            expect(true).toBe(false);
          }

          // The below test has been replaced by above trickery:
          //
          //     expect($('.vidtime')).toHaveHtml('1:00 / 1:01');
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

        it('add the video-fullscreen class', function() {
          expect(state.el).toHaveClass('video-fullscreen');
        });

        it('tell VideoCaption to resize', function() {
          expect(videoCaption.resize).toHaveBeenCalled();
        });
      });

      describe('when the video player already full screen', function() {
        beforeEach(function() {
          initialize();
          spyOn(videoCaption, 'resize').andCallThrough();

          state.el.addClass('video-fullscreen');
          videoControl.fullScreenState = true;
          isFullScreen = true;
          videoControl.fullScreenEl.attr('title', 'Exit-fullscreen');

          videoControl.toggleFullScreen(jQuery.Event("click"));
        });

        it('replace the full screen button tooltip', function() {
          expect($('.add-fullscreen')).toHaveAttr('title', 'Fullscreen');
        });

        it('remove the video-fullscreen class', function() {
          expect(state.el).not.toHaveClass('video-fullscreen');
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
