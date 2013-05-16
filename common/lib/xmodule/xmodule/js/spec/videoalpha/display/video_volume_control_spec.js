(function() {
  describe('VideoVolumeControlAlpha', function() {
    var state, player;

    describe('constructor', function() {
      beforeEach(function() {
        // spyOn($.fn, 'slider');
        state = jasmine.stubVideoPlayerAlpha(this);
        player = state.videoPlayer.player;
      });

      it('initialize currentVolume to 100', function() {
        return expect(state.videoVolumeControl.currentVolume).toEqual(1);
      });
      it('render the volume control', function() {
        return expect($('.secondary-controls').html()).toContain("<div class=\"volume\">\n  <a href=\"#\"></a>\n  <div class=\"volume-slider-container\">\n    <div class=\"volume-slider\"></div>\n  </div>\n</div>");
      });
      it('create the slider', function() {
        return expect($.fn.slider).toHaveBeenCalledWith({
          orientation: "vertical",
          range: "min",
          min: 0,
          max: 100,
          value: 100,
          change: this.volumeControl.onChange,
          slide: this.volumeControl.onChange
        });
      });
      return it('bind the volume control', function() {
        expect($('.volume>a')).toHandleWith('click', this.volumeControl.toggleMute);
        expect($('.volume')).not.toHaveClass('open');
        $('.volume').mouseenter();
        expect($('.volume')).toHaveClass('open');
        $('.volume').mouseleave();
        return expect($('.volume')).not.toHaveClass('open');
      });
    });
    describe('onChange', function() {
      beforeEach(function() {
        var _this = this;
        spyOnEvent(this.volumeControl, 'volumeChange');
        this.newVolume = void 0;
        this.volumeControl = new VideoVolumeControlAlpha({
          el: $('.secondary-controls')
        });
        return $(this.volumeControl).bind('volumeChange', function(event, volume) {
          return _this.newVolume = volume;
        });
      });
      describe('when the new volume is more than 0', function() {
        beforeEach(function() {
          return this.volumeControl.onChange(void 0, {
            value: 60
          });
        });
        it('set the player volume', function() {
          return expect(this.newVolume).toEqual(60);
        });
        return it('remote muted class', function() {
          return expect($('.volume')).not.toHaveClass('muted');
        });
      });
      return describe('when the new volume is 0', function() {
        beforeEach(function() {
          return this.volumeControl.onChange(void 0, {
            value: 0
          });
        });
        it('set the player volume', function() {
          return expect(this.newVolume).toEqual(0);
        });
        return it('add muted class', function() {
          return expect($('.volume')).toHaveClass('muted');
        });
      });
    });
    return describe('toggleMute', function() {
      beforeEach(function() {
        var _this = this;
        this.newVolume = void 0;
        this.volumeControl = new VideoVolumeControlAlpha({
          el: $('.secondary-controls')
        });
        return $(this.volumeControl).bind('volumeChange', function(event, volume) {
          return _this.newVolume = volume;
        });
      });
      describe('when the current volume is more than 0', function() {
        beforeEach(function() {
          this.volumeControl.currentVolume = 60;
          return this.volumeControl.toggleMute();
        });
        it('save the previous volume', function() {
          return expect(this.volumeControl.previousVolume).toEqual(60);
        });
        return it('set the player volume', function() {
          return expect(this.newVolume).toEqual(0);
        });
      });
      return describe('when the current volume is 0', function() {
        beforeEach(function() {
          this.volumeControl.currentVolume = 0;
          this.volumeControl.previousVolume = 60;
          return this.volumeControl.toggleMute();
        });
        return it('set the player volume to previous volume', function() {
          return expect(this.newVolume).toEqual(60);
        });
      });
    });
  });

}).call(this);
