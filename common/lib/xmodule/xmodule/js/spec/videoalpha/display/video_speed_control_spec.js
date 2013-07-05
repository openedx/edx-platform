(function() {
  describe('VideoSpeedControlAlpha', function() {
    var state, videoPlayer, videoControl, videoSpeedControl;

    function initialize() {
      loadFixtures('videoalpha_all.html');
      state = new VideoAlpha('#example');
      videoPlayer = state.videoPlayer;
      videoControl = state.videoControl;
      videoSpeedControl = state.videoSpeedControl;
    }

    beforeEach(function() {
      window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn(false);
    });

    describe('constructor', function() {
      describe('always', function() {
        beforeEach(function() {
          initialize();
        });

        it('add the video speed control to player', function() {
          var li, secondaryControls;
          secondaryControls = $('.secondary-controls');
          li = secondaryControls.find('.video_speeds li');
          expect(secondaryControls).toContain('.speeds');
          expect(secondaryControls).toContain('.video_speeds');
          expect(secondaryControls.find('p.active').text()).toBe('1.0x');
          expect(li.filter('.active')).toHaveData('speed', videoSpeedControl.currentSpeed);
          expect(li.length).toBe(videoSpeedControl.speeds.length);
          $.each(li.toArray().reverse(), function(index, link) {
            expect($(link)).toHaveData('speed', videoSpeedControl.speeds[index]);
            // TODO: Fails
            expect($(link).find('a').text()).toBe(videoSpeedControl.speeds[index] + 'x');
          });
        });

        it('bind to change video speed link', function() {
          // TODO: Fails
          expect($('.video_speeds a')).toHandleWith('click', videoSpeedControl.changeVideoSpeed);
        });
      });

      describe('when running on touch based device', function() {
        beforeEach(function() {
          window.onTouchBasedDevice.andReturn(true);
          initialize();
        });

        it('open the speed toggle on click', function() {
          $('.speeds').click();
          expect($('.speeds')).toHaveClass('open');
          $('.speeds').click();
          expect($('.speeds')).not.toHaveClass('open');
        });
      });
      
      describe('when running on non-touch based device', function() {
        beforeEach(function() {
          initialize();
        });

        it('open the speed toggle on hover', function() {
          $('.speeds').mouseenter();
          expect($('.speeds')).toHaveClass('open');
          $('.speeds').mouseleave();
          expect($('.speeds')).not.toHaveClass('open');
        });

        it('close the speed toggle on mouse out', function() {
          $('.speeds').mouseenter().mouseleave();
          expect($('.speeds')).not.toHaveClass('open');
        });

        it('close the speed toggle on click', function() {
          $('.speeds').mouseenter().click();
          expect($('.speeds')).not.toHaveClass('open');
        });
      });
    });

    describe('changeVideoSpeed', function() {
      beforeEach(function() {
        initialize();
        videoSpeedControl.setSpeed(1.0);
      });

      describe('when new speed is the same', function() {
        beforeEach(function() {
          spyOnEvent(videoPlayer, 'onSpeedChange');
          $('li[data-speed="1.0"] a').click();
        });
        
        it('does not trigger speedChange event', function() {
          expect('onSpeedChange').not.toHaveBeenTriggeredOn(videoPlayer);
        });
      });
      
      describe('when new speed is not the same', function() {
        beforeEach(function() {
          spyOnEvent(videoPlayer, 'onSpeedChange');
          $('li[data-speed="0.75"] a').click();
        });

        it('trigger speedChange event', function() {
          // TODO: Fails
          expect('onSpeedChange').toHaveBeenTriggeredOn(videoPlayer);
          // TODO: Fails
          expect(videoSpeedControl.currentSpeed).toEqual(0.75);
        });
      });
    });
    
    describe('onSpeedChange', function() {
      beforeEach(function() {
        initialize();
        $('li[data-speed="1.0"] a').addClass('active');
        videoSpeedControl.setSpeed(0.75);
      });
      
      it('set the new speed as active', function() {
        expect($('.video_speeds li[data-speed="1.0"]')).not.toHaveClass('active');
        expect($('.video_speeds li[data-speed="0.75"]')).toHaveClass('active');
        expect($('.speeds p.active')).toHaveHtml('0.75x');
      });
    });
  });

}).call(this);
