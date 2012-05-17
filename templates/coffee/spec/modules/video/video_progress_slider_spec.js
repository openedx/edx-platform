(function() {

  describe('VideoProgressSlider', function() {
    beforeEach(function() {
      return this.player = jasmine.stubVideoPlayer(this);
    });
    describe('constructor', function() {
      beforeEach(function() {
        spyOn($.fn, 'slider').andCallThrough();
        return this.slider = new VideoProgressSlider(this.player);
      });
      it('build the slider', function() {
        expect(this.slider.slider).toBe('.slider');
        return expect($.fn.slider).toHaveBeenCalledWith({
          range: 'min',
          change: this.slider.onChange,
          slide: this.slider.onSlide,
          stop: this.slider.onStop
        });
      });
      it('build the seek handle', function() {
        expect(this.slider.handle).toBe('.ui-slider-handle');
        return expect($.fn.qtip).toHaveBeenCalledWith({
          content: "0:00",
          position: {
            my: 'bottom center',
            at: 'top center',
            container: this.slider.handle
          },
          hide: {
            delay: 700
          },
          style: {
            classes: 'ui-tooltip-slider',
            widget: true
          }
        });
      });
      return it('bind player events', function() {
        return expect($(this.player)).toHandleWith('updatePlayTime', this.slider.onUpdatePlayTime);
      });
    });
    describe('onReady', function() {
      beforeEach(function() {
        spyOn(this.player, 'duration').andReturn(120);
        this.slider = new VideoProgressSlider(this.player);
        return this.slider.onReady();
      });
      return it('set the max value to the length of video', function() {
        return expect(this.slider.slider.slider('option', 'max')).toEqual(120);
      });
    });
    describe('onUpdatePlayTime', function() {
      beforeEach(function() {
        this.slider = new VideoProgressSlider(this.player);
        spyOn(this.player, 'duration').andReturn(120);
        return spyOn($.fn, 'slider').andCallThrough();
      });
      describe('when frozen', function() {
        beforeEach(function() {
          this.slider.frozen = true;
          return this.slider.onUpdatePlayTime({}, 20);
        });
        return it('does not update the slider', function() {
          return expect($.fn.slider).not.toHaveBeenCalled();
        });
      });
      return describe('when not frozen', function() {
        beforeEach(function() {
          this.slider.frozen = false;
          return this.slider.onUpdatePlayTime({}, 20);
        });
        it('update the max value of the slider', function() {
          return expect($.fn.slider).toHaveBeenCalledWith('option', 'max', 120);
        });
        return it('update current value of the slider', function() {
          return expect($.fn.slider).toHaveBeenCalledWith('value', 20);
        });
      });
    });
    describe('onSlide', function() {
      beforeEach(function() {
        var _this = this;
        this.slider = new VideoProgressSlider(this.player);
        this.time = null;
        $(this.player).bind('seek', function(event, time) {
          return _this.time = time;
        });
        spyOnEvent(this.player, 'seek');
        return this.slider.onSlide({}, {
          value: 20
        });
      });
      it('freeze the slider', function() {
        return expect(this.slider.frozen).toBeTruthy();
      });
      it('update the tooltip', function() {
        return expect($.fn.qtip).toHaveBeenCalled();
      });
      return it('trigger seek event', function() {
        expect('seek').toHaveBeenTriggeredOn(this.player);
        return expect(this.time).toEqual(20);
      });
    });
    describe('onChange', function() {
      beforeEach(function() {
        this.slider = new VideoProgressSlider(this.player);
        return this.slider.onChange({}, {
          value: 20
        });
      });
      return it('update the tooltip', function() {
        return expect($.fn.qtip).toHaveBeenCalled();
      });
    });
    describe('onStop', function() {
      beforeEach(function() {
        var _this = this;
        this.slider = new VideoProgressSlider(this.player);
        this.time = null;
        $(this.player).bind('seek', function(event, time) {
          return _this.time = time;
        });
        spyOnEvent(this.player, 'seek');
        spyOn(window, 'setTimeout');
        return this.slider.onStop({}, {
          value: 20
        });
      });
      it('freeze the slider', function() {
        return expect(this.slider.frozen).toBeTruthy();
      });
      it('trigger seek event', function() {
        expect('seek').toHaveBeenTriggeredOn(this.player);
        return expect(this.time).toEqual(20);
      });
      return it('set timeout to unfreeze the slider', function() {
        expect(window.setTimeout).toHaveBeenCalledWith(jasmine.any(Function), 200);
        window.setTimeout.mostRecentCall.args[0]();
        return expect(this.slider.frozen).toBeFalsy();
      });
    });
    return describe('updateTooltip', function() {
      beforeEach(function() {
        this.slider = new VideoProgressSlider(this.player);
        return this.slider.updateTooltip(90);
      });
      return it('set the tooltip value', function() {
        return expect($.fn.qtip).toHaveBeenCalledWith('option', 'content.text', '1:30');
      });
    });
  });

}).call(this);
