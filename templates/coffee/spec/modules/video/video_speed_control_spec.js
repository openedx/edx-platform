(function() {

  describe('VideoSpeedControl', function() {
    beforeEach(function() {
      this.player = jasmine.stubVideoPlayer(this);
      return $('.speeds').remove();
    });
    afterEach(function() {});
    describe('constructor', function() {
      describe('always', function() {
        beforeEach(function() {
          return this.speedControl = new VideoSpeedControl(this.player, this.video.speeds);
        });
        it('add the video speed control to player', function() {
          return expect($('.secondary-controls').html()).toContain('<div class="speeds">\n  <a href="#">\n    <h3>Speed</h3>\n    <p class="active">1.0x</p>\n  </a>\n  <ol class="video_speeds"><li data-speed="1.0" class="active"><a href="#">1.0x</a></li><li data-speed="0.75"><a href="#">0.75x</a></li></ol>\n</div>');
        });
        it('bind to player speedChange event', function() {
          return expect($(this.player)).toHandleWith('speedChange', this.speedControl.onSpeedChange);
        });
        return it('bind to change video speed link', function() {
          return expect($('.video_speeds a')).toHandleWith('click', this.speedControl.changeVideoSpeed);
        });
      });
      describe('when running on touch based device', function() {
        beforeEach(function() {
          spyOn(window, 'onTouchBasedDevice').andReturn(true);
          $('.speeds').removeClass('open');
          return this.speedControl = new VideoSpeedControl(this.player, this.video.speeds);
        });
        return it('open the speed toggle on click', function() {
          $('.speeds').click();
          expect($('.speeds')).toHaveClass('open');
          $('.speeds').click();
          return expect($('.speeds')).not.toHaveClass('open');
        });
      });
      return describe('when running on non-touch based device', function() {
        beforeEach(function() {
          spyOn(window, 'onTouchBasedDevice').andReturn(false);
          $('.speeds').removeClass('open');
          return this.speedControl = new VideoSpeedControl(this.player, this.video.speeds);
        });
        it('open the speed toggle on hover', function() {
          $('.speeds').mouseover();
          expect($('.speeds')).toHaveClass('open');
          $('.speeds').mouseout();
          return expect($('.speeds')).not.toHaveClass('open');
        });
        it('close the speed toggle on mouse out', function() {
          $('.speeds').mouseover().mouseout();
          return expect($('.speeds')).not.toHaveClass('open');
        });
        return it('close the speed toggle on click', function() {
          $('.speeds').mouseover().click();
          return expect($('.speeds')).not.toHaveClass('open');
        });
      });
    });
    describe('changeVideoSpeed', function() {
      beforeEach(function() {
        this.speedControl = new VideoSpeedControl(this.player, this.video.speeds);
        return this.video.setSpeed('1.0');
      });
      describe('when new speed is the same', function() {
        beforeEach(function() {
          spyOnEvent(this.player, 'speedChange');
          return $('li[data-speed="1.0"] a').click();
        });
        return it('does not trigger speedChange event', function() {
          return expect('speedChange').not.toHaveBeenTriggeredOn(this.player);
        });
      });
      return describe('when new speed is not the same', function() {
        beforeEach(function() {
          var _this = this;
          this.newSpeed = null;
          $(this.player).bind('speedChange', function(event, newSpeed) {
            return _this.newSpeed = newSpeed;
          });
          spyOnEvent(this.player, 'speedChange');
          return $('li[data-speed="0.75"] a').click();
        });
        return it('trigger player speedChange event', function() {
          expect('speedChange').toHaveBeenTriggeredOn(this.player);
          return expect(this.newSpeed).toEqual(0.75);
        });
      });
    });
    return describe('onSpeedChange', function() {
      beforeEach(function() {
        this.speedControl = new VideoSpeedControl(this.player, this.video.speeds);
        $('li[data-speed="1.0"] a').addClass('active');
        return this.speedControl.setSpeed('0.75');
      });
      return it('set the new speed as active', function() {
        expect($('.video_speeds li[data-speed="1.0"]')).not.toHaveClass('active');
        expect($('.video_speeds li[data-speed="0.75"]')).toHaveClass('active');
        return expect($('.speeds p.active')).toHaveHtml('0.75x');
      });
    });
  });

}).call(this);
