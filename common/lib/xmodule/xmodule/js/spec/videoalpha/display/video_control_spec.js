(function() {
  describe('VideoControlAlpha', function() {
    var state, videoControl;

    function initialize() {
      loadFixtures('videoalpha_all.html');
      state = new VideoAlpha('#example');
      videoControl = state.videoControl;
    }

    describe('constructor', function() {
      beforeEach(function() {
        window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn(false);
        initialize();
      });

      it('render the video controls', function() {
        expect($('.video-controls')).toContain(
          ['.slider', 'ul.vcr', 'a.play', '.vidtime', '.add-fullscreen'].join(',')
        ); //Should we add '.quality_control' and '.hide-subtitles'?
        expect($('.video-controls').find('.vidtime')).toHaveText('0:00 / 0:00');
      });

      it('bind the playback button', function() {
        expect($('.video_control')).toHandleWith('click', videoControl.togglePlayback);
      });

      describe('when on a non-touch based device', function() {
        beforeEach(function() {
          initialize();
        });

        it('add the play class to video control', function() {
          expect($('.video_control')).toHaveClass('play');
          expect($('.video_control')).toHaveAttr('title', 'Play');
        });
      });

      describe('when on a touch based device', function() {
        beforeEach(function() {
          window.onTouchBasedDevice.andReturn(true);
          initialize();
        });

        it('does not add the play class to video control', function() {
          expect($('.video_control')).not.toHaveClass('play');
          expect($('.video_control')).not.toHaveAttr('title', 'Play');
        });
      });
    });

    describe('play', function() {
      beforeEach(function() {
        initialize();
        videoControl.play();
      });

      it('switch playback button to play state', function() {
        expect($('.video_control')).not.toHaveClass('play');
        expect($('.video_control')).toHaveClass('pause');
        expect($('.video_control')).toHaveAttr('title', 'Pause');
      });
    });

    describe('pause', function() {
      beforeEach(function() {
        initialize();
        videoControl.pause();
      });

      it('switch playback button to pause state', function() {
        expect($('.video_control')).not.toHaveClass('pause');
        expect($('.video_control')).toHaveClass('play');
        expect($('.video_control')).toHaveAttr('title', 'Play');
      });
    });

    describe('togglePlayback', function() {
      beforeEach(function() {
        initialize();
      });

      describe('when the control does not have play or pause class', function() {
        beforeEach(function() {
          $('.video_control').removeClass('play').removeClass('pause');
        });

        describe('when the video is playing', function() {
          beforeEach(function() {
            $('.video_control').addClass('play');
            spyOnEvent(videoControl, 'pause');
            videoControl.togglePlayback(jQuery.Event('click'));
          });

          it('does not trigger the pause event', function() {
            expect('pause').not.toHaveBeenTriggeredOn(videoControl);
          });
        });

        describe('when the video is paused', function() {
          beforeEach(function() {
            $('.video_control').addClass('pause');
            spyOnEvent(videoControl, 'play');
            videoControl.togglePlayback(jQuery.Event('click'));
          });

          it('does not trigger the play event', function() {
            expect('play').not.toHaveBeenTriggeredOn(videoControl);
          });
        });
      });
    });
  });

}).call(this);
