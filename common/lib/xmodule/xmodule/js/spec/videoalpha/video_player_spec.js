(function() {
  describe('VideoPlayerAlpha', function() {
    var state, videoPlayer, player, videoControl, videoCaption, videoProgressSlider, videoSpeedControl, videoVolumeControl;

    function initialize(fixture) {
      if (typeof fixture === 'undefined') {
        loadFixtures('videoalpha_all.html');
      } else {
        loadFixtures(fixture);
      }

      state = new VideoAlpha('#example');
      videoPlayer = state.videoPlayer;
      player = videoPlayer.player;
      videoControl = state.videoControl;
      videoCaption = state.videoCaption;
      videoProgressSlider = state.videoProgressSlider;
      videoSpeedControl = state.videoSpeedControl;
      videoVolumeControl = state.videoVolumeControl;
    }

    function initializeYouTube() {
        initialize('videoalpha.html');
    }

    afterEach(function() {
       $('source').remove();
    });

    describe('constructor', function() {
      beforeEach(function() {
        $.fn.qtip.andCallFake(function() {
          $(this).data('qtip', true);
        });
      });

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
          expect(state.youtubeId()).toEqual('test_name_of_the_subtitles');
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
          console.log('videoProgressSlider', videoProgressSlider, state, state.videoControl.sliderEl)
          expect(videoProgressSlider.el).toHaveClass('slider');
        });

        // All the toHandleWith() expect tests are not necessary for this version of Video Alpha.
        // jQuery event system is not used to trigger and invoke methods. This is an artifact from
        // previous version of Video Alpha.
        //
        // xit('bind to video control play event', function() {
        //   expect($(videoControl)).toHandleWith('play', player.play);
        // });
        //
        // xit('bind to video control pause event', function() {
        //   expect($(videoControl)).toHandleWith('pause', player.pause);
        // });
        //
        // xit('bind to video caption seek event', function() {
        //   expect($(videoCaption)).toHandleWith('caption_seek', player.onSeek);
        // });
        //
        // xit('bind to video speed control speedChange event', function() {
        //   expect($(videoSpeedControl)).toHandleWith('speedChange', player.onSpeedChange);
        // });
        //
        // xit('bind to video progress slider seek event', function() {
        //   expect($(videoProgressSlider)).toHandleWith('slide_seek', player.onSeek);
        // });
        //
        // xit('bind to video volume control volumeChange event', function() {
        //   expect($(videoVolumeControl)).toHandleWith('volumeChange', player.onVolumeChange);
        // });
        //
        // xit('bind to key press', function() {
        //   expect($(document.documentElement)).toHandleWith('keyup', player.bindExitFullScreen);
        // });
        //
        // xit('bind to fullscreen switching button', function() {
        //   expect($('.add-fullscreen')).toHandleWith('click', player.toggleFullScreen);
        // });
      });

      it('create Youtube player', function() {
        var oldYT = window.YT;

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
          videoId: 'normalSpeedYoutubeId',
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
      //
      // xit('create HTML5 player', function() {
      //   spyOn(state.HTML5Video, 'Player').andCallThrough();
      //   initialize();
      //
      //   expect(window.HTML5Video.Player).toHaveBeenCalledWith(this.video.el, {
      //     playerVars: playerVars,
      //     videoSources: this.video.html5Sources,
      //     events: {
      //       onReady: player.onReady,
      //       onStateChange: player.onStateChange
      //     }
      //   });
      // });

      describe('when not on a touch based device', function() {
        var oldOTBD;

        beforeEach(function() {
          oldOTBD = window.onTouchBasedDevice;

          window.onTouchBasedDevice = function () {
            return true;
          };

          initialize();
        });

        afterEach(function () {
            window.onTouchBasedDevice = oldOTBD;
        });

        it('does not add the tooltip to fullscreen button', function() {
          expect($('.add-fullscreen')).not.toHaveData('qtip');
        });

        it('create video volume control', function() {
          expect(videoVolumeControl).toBeDefined();
          expect(videoVolumeControl.el).toHaveClass('volume');
        });
      });

      describe('when on a touch based device', function() {
        var oldOTBD;

        beforeEach(function() {
          oldOTBD = window.onTouchBasedDevice;

          window.onTouchBasedDevice = function () {
            return false;
          };

          initialize();
        });

        afterEach(function () {
            window.onTouchBasedDevice = oldOTBD;
        });

        it('add the tooltip to fullscreen button', function() {
          expect($('.add-fullscreen')).toHaveData('qtip');
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

          // The below test has been replaced by above trickery.
          // expect($('.vidtime')).toHaveHtml('1:00 / 1:01');
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
        expect(Number(player.getVolume().toFixed(1)).toEqual(0.6);
      });
    });
  });

}).call(this);
