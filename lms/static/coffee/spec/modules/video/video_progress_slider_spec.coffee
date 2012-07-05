describe 'VideoProgressSlider', ->
  beforeEach ->
    jasmine.stubVideoPlayer @

  describe 'constructor', ->
    describe 'on a non-touch based device', ->
      beforeEach ->
        spyOn($.fn, 'slider').andCallThrough()
        spyOn(window, 'onTouchBasedDevice').andReturn false
        @slider = new VideoProgressSlider el: $('.slider')

      it 'build the slider', ->
        expect(@slider.slider).toBe '.slider'
        expect($.fn.slider).toHaveBeenCalledWith
          range: 'min'
          change: @slider.onChange
          slide: @slider.onSlide
          stop: @slider.onStop

      it 'build the seek handle', ->
        expect(@slider.handle).toBe '.slider .ui-slider-handle'
        expect($.fn.qtip).toHaveBeenCalledWith
          content: "0:00"
          position:
            my: 'bottom center'
            at: 'top center'
            container: @slider.handle
          hide:
            delay: 700
          style:
            classes: 'ui-tooltip-slider'
            widget: true

    describe 'on a touch-based device', ->
      beforeEach ->
        spyOn($.fn, 'slider').andCallThrough()
        spyOn(window, 'onTouchBasedDevice').andReturn true
        @slider = new VideoProgressSlider el: $('.slider')

      it 'does not build the slider', ->
        expect(@slider.slider).toBeUndefined
        expect($.fn.slider).not.toHaveBeenCalled()

  describe 'play', ->
    beforeEach ->
      @slider = new VideoProgressSlider el: $('.slider')
      spyOn($.fn, 'slider').andCallThrough()

    describe 'when the slider was already built', ->
      beforeEach ->
        @slider.play()

      it 'does not build the slider', ->
        expect($.fn.slider).not.toHaveBeenCalled

    describe 'when the slider was not already built', ->
      beforeEach ->
        @slider.slider = null
        @slider.play()

      it 'build the slider', ->
        expect(@slider.slider).toBe '.slider'
        expect($.fn.slider).toHaveBeenCalledWith
          range: 'min'
          change: @slider.onChange
          slide: @slider.onSlide
          stop: @slider.onStop

      it 'build the seek handle', ->
        expect(@slider.handle).toBe '.ui-slider-handle'
        expect($.fn.qtip).toHaveBeenCalledWith
          content: "0:00"
          position:
            my: 'bottom center'
            at: 'top center'
            container: @slider.handle
          hide:
            delay: 700
          style:
            classes: 'ui-tooltip-slider'
            widget: true

  describe 'updatePlayTime', ->
    beforeEach ->
      @slider = new VideoProgressSlider el: $('.slider')
      spyOn($.fn, 'slider').andCallThrough()

    describe 'when frozen', ->
      beforeEach ->
        @slider.frozen = true
        @slider.updatePlayTime 20, 120

      it 'does not update the slider', ->
        expect($.fn.slider).not.toHaveBeenCalled()

    describe 'when not frozen', ->
      beforeEach ->
        @slider.frozen = false
        @slider.updatePlayTime 20, 120

      it 'update the max value of the slider', ->
        expect($.fn.slider).toHaveBeenCalledWith 'option', 'max', 120

      it 'update current value of the slider', ->
        expect($.fn.slider).toHaveBeenCalledWith 'value', 20

  describe 'onSlide', ->
    beforeEach ->
      @slider = new VideoProgressSlider el: $('.slider')
      @time = null
      $(@slider).bind 'seek', (event, time) => @time = time
      spyOnEvent @slider, 'seek'
      @slider.onSlide {}, value: 20

    it 'freeze the slider', ->
      expect(@slider.frozen).toBeTruthy()

    it 'update the tooltip', ->
      expect($.fn.qtip).toHaveBeenCalled()

    it 'trigger seek event', ->
      expect('seek').toHaveBeenTriggeredOn @slider
      expect(@time).toEqual 20

  describe 'onChange', ->
    beforeEach ->
      @slider = new VideoProgressSlider el: $('.slider')
      @slider.onChange {}, value: 20

    it 'update the tooltip', ->
      expect($.fn.qtip).toHaveBeenCalled()

  describe 'onStop', ->
    beforeEach ->
      @slider = new VideoProgressSlider el: $('.slider')
      @time = null
      $(@slider).bind 'seek', (event, time) => @time = time
      spyOnEvent @slider, 'seek'
      spyOn(window, 'setTimeout')
      @slider.onStop {}, value: 20

    it 'freeze the slider', ->
      expect(@slider.frozen).toBeTruthy()

    it 'trigger seek event', ->
      expect('seek').toHaveBeenTriggeredOn @slider
      expect(@time).toEqual 20

    it 'set timeout to unfreeze the slider', ->
      expect(window.setTimeout).toHaveBeenCalledWith jasmine.any(Function), 200
      window.setTimeout.mostRecentCall.args[0]()
      expect(@slider.frozen).toBeFalsy()

  describe 'updateTooltip', ->
    beforeEach ->
      @slider = new VideoProgressSlider el: $('.slider')
      @slider.updateTooltip 90

    it 'set the tooltip value', ->
      expect($.fn.qtip).toHaveBeenCalledWith 'option', 'content.text', '1:30'
