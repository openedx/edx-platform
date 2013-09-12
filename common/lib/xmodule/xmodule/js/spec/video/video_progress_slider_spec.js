(function() {
  describe('VideoProgressSlider', function() {
    var state, videoPlayer, videoProgressSlider, oldOTBD;

    function initialize() {
      loadFixtures('video_all.html');
      state = new Video('#example');
      videoPlayer = state.videoPlayer;
      videoProgressSlider = state.videoProgressSlider;
    }

    beforeEach(function() {
        oldOTBD = window.onTouchBasedDevice;
        window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn(false);
    });


    afterEach(function() {
        $('source').remove();
        window.onTouchBasedDevice = oldOTBD;
    });

    describe('constructor', function() {
      describe('on a non-touch based device', function() {
        beforeEach(function() {
          spyOn($.fn, 'slider').andCallThrough();
          initialize();
        });

        it('build the slider', function() {
          expect(videoProgressSlider.slider).toBe('.slider');
          expect($.fn.slider).toHaveBeenCalledWith({
            range: 'min',
            change: videoProgressSlider.onChange,
            slide: videoProgressSlider.onSlide,
            stop: videoProgressSlider.onStop
          });
        });

        it('build the seek handle', function() {
          expect(videoProgressSlider.handle).toBe('.slider .ui-slider-handle');
        });
      });

      describe('on a touch-based device', function() {
        beforeEach(function() {
          window.onTouchBasedDevice.andReturn(true);
          spyOn($.fn, 'slider').andCallThrough();
          initialize();
        });

        it('does not build the slider', function() {
          expect(videoProgressSlider.slider).toBeUndefined();

          // We can't expect $.fn.slider not to have been called,
          // because sliders are used in other parts of Video.
        });
      });
    });

    describe('play', function() {
      beforeEach(function() {
        initialize();
      });

      describe('when the slider was already built', function() {
        var spy;

        beforeEach(function() {
          spy = spyOn(videoProgressSlider, 'buildSlider');
          spy.andCallThrough();
          videoPlayer.play();
        });

        it('does not build the slider', function() {
          expect(spy.callCount).toEqual(0);
        });
      });

      // Currently, the slider is not rebuilt if it does not exist.
    });

    describe('updatePlayTime', function() {
      beforeEach(function() {
        initialize();
      });

      describe('when frozen', function() {
        beforeEach(function() {
          spyOn($.fn, 'slider').andCallThrough();
          videoProgressSlider.frozen = true;
          videoProgressSlider.updatePlayTime(20, 120);
        });

        it('does not update the slider', function() {
          expect($.fn.slider).not.toHaveBeenCalled();
        });
      });

      describe('when not frozen', function() {
        beforeEach(function() {
          spyOn($.fn, 'slider').andCallThrough();
          videoProgressSlider.frozen = false;
          videoProgressSlider.updatePlayTime({time:20, duration:120});
        });

        it('update the max value of the slider', function() {
          expect($.fn.slider).toHaveBeenCalledWith('option', 'max', 120);
        });

        it('update current value of the slider', function() {
          expect($.fn.slider).toHaveBeenCalledWith('option', 'value', 20);
        });
      });
    });

    describe('onSlide', function() {
      beforeEach(function() {
        initialize();
        spyOn($.fn, 'slider').andCallThrough();
        spyOn(videoPlayer, 'onSlideSeek').andCallThrough();
        videoProgressSlider.onSlide({}, {
          value: 20
        });
      });

      it('freeze the slider', function() {
        expect(videoProgressSlider.frozen).toBeTruthy();
      });

      it('trigger seek event', function() {
        expect(videoPlayer.onSlideSeek).toHaveBeenCalled();
        expect(videoPlayer.currentTime).toEqual(20);
      });
    });

    describe('onChange', function() {
      beforeEach(function() {
        initialize();
        spyOn($.fn, 'slider').andCallThrough();
        videoProgressSlider.onChange({}, {
          value: 20
        });
      });
    });

    describe('onStop', function() {
      beforeEach(function() {
        initialize();
        spyOn(videoPlayer, 'onSlideSeek').andCallThrough();
        videoProgressSlider.onStop({}, {
          value: 20
        });
      });

      it('freeze the slider', function() {
        expect(videoProgressSlider.frozen).toBeTruthy();
      });

      it('trigger seek event', function() {
        expect(videoPlayer.onSlideSeek).toHaveBeenCalled();
        expect(videoPlayer.currentTime).toEqual(20);
      });

      it('set timeout to unfreeze the slider', function() {
        expect(window.setTimeout).toHaveBeenCalledWith(jasmine.any(Function), 200);
        window.setTimeout.mostRecentCall.args[0]();
        expect(videoProgressSlider.frozen).toBeFalsy();
      });
    });
  });

}).call(this);
