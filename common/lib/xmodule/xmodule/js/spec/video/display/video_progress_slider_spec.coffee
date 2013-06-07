describe 'VideoProgressSlider', ->
  beforeEach ->
    window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn false

  describe 'constructor', ->
    describe 'on a non-touch based device', ->
      beforeEach ->
        spyOn($.fn, 'slider').andCallThrough()
        @player = jasmine.stubVideoPlayer @
        @progressSlider = @player.progressSlider

      it 'build the slider', ->
        expect(@progressSlider.slider).toBe '.slider'
        expect($.fn.slider).toHaveBeenCalledWith
          range: 'min'
          change: @progressSlider.onChange
          slide: @progressSlider.onSlide
          stop: @progressSlider.onStop

      it 'build the seek handle', ->
        expect(@progressSlider.handle).toBe '.slider .ui-slider-handle'
        expect($.fn.qtip).toHaveBeenCalledWith
          content: "0:00"
          position:
            my: 'bottom center'
            at: 'top center'
            container: @progressSlider.handle
          hide:
            delay: 700
          style:
            classes: 'ui-tooltip-slider'
            widget: true

    describe 'on a touch-based device', ->
      beforeEach ->
        window.onTouchBasedDevice.andReturn true
        spyOn($.fn, 'slider').andCallThrough()
        @player = jasmine.stubVideoPlayer @
        @progressSlider = @player.progressSlider

      it 'does not build the slider', ->
        expect(@progressSlider.slider).toBeUndefined
        expect($.fn.slider).not.toHaveBeenCalled()

  describe 'play', ->
    beforeEach ->
      spyOn(VideoProgressSlider.prototype, 'buildSlider').andCallThrough()
      @player = jasmine.stubVideoPlayer @
      @progressSlider = @player.progressSlider

    describe 'when the slider was already built', ->

      beforeEach ->
        @progressSlider.play()

      it 'does not build the slider', ->
        expect(@progressSlider.buildSlider.calls.length).toEqual 1

    describe 'when the slider was not already built', ->
      beforeEach ->
        spyOn($.fn, 'slider').andCallThrough()
        @progressSlider.slider = null
        @progressSlider.play()

      it 'build the slider', ->
        expect(@progressSlider.slider).toBe '.slider'
        expect($.fn.slider).toHaveBeenCalledWith
          range: 'min'
          change: @progressSlider.onChange
          slide: @progressSlider.onSlide
          stop: @progressSlider.onStop

      it 'build the seek handle', ->
        expect(@progressSlider.handle).toBe '.ui-slider-handle'
        expect($.fn.qtip).toHaveBeenCalledWith
          content: "0:00"
          position:
            my: 'bottom center'
            at: 'top center'
            container: @progressSlider.handle
          hide:
            delay: 700
          style:
            classes: 'ui-tooltip-slider'
            widget: true

  describe 'updatePlayTime', ->
    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @progressSlider = @player.progressSlider

    describe 'when frozen', ->
      beforeEach ->
        spyOn($.fn, 'slider').andCallThrough()
        @progressSlider.frozen = true
        @progressSlider.updatePlayTime 20, 120

      it 'does not update the slider', ->
        expect($.fn.slider).not.toHaveBeenCalled()

    describe 'when not frozen', ->
      beforeEach ->
        spyOn($.fn, 'slider').andCallThrough()
        @progressSlider.frozen = false
        @progressSlider.updatePlayTime 20, 120

      it 'update the max value of the slider', ->
        expect($.fn.slider).toHaveBeenCalledWith 'option', 'max', 120

      it 'update current value of the slider', ->
        expect($.fn.slider).toHaveBeenCalledWith 'value', 20

  describe 'onSlide', ->
    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @progressSlider = @player.progressSlider
      @time = null
      $(@progressSlider).bind 'seek', (event, time) => @time = time
      spyOnEvent @progressSlider, 'seek'
      @progressSlider.onSlide {}, value: 20

    it 'freeze the slider', ->
      expect(@progressSlider.frozen).toBeTruthy()

    it 'update the tooltip', ->
      expect($.fn.qtip).toHaveBeenCalled()

    it 'trigger seek event', ->
      expect('seek').toHaveBeenTriggeredOn @progressSlider
      expect(@time).toEqual 20

  describe 'onChange', ->
    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @progressSlider = @player.progressSlider
      @progressSlider.onChange {}, value: 20

    it 'update the tooltip', ->
      expect($.fn.qtip).toHaveBeenCalled()

  describe 'onStop', ->
    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @progressSlider = @player.progressSlider
      @time = null
      $(@progressSlider).bind 'seek', (event, time) => @time = time
      spyOnEvent @progressSlider, 'seek'
      @progressSlider.onStop {}, value: 20

    it 'freeze the slider', ->
      expect(@progressSlider.frozen).toBeTruthy()

    it 'trigger seek event', ->
      expect('seek').toHaveBeenTriggeredOn @progressSlider
      expect(@time).toEqual 20

    it 'set timeout to unfreeze the slider', ->
      expect(window.setTimeout).toHaveBeenCalledWith jasmine.any(Function), 200
      window.setTimeout.mostRecentCall.args[0]()
      expect(@progressSlider.frozen).toBeFalsy()

  describe 'updateTooltip', ->
    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @progressSlider = @player.progressSlider
      @progressSlider.updateTooltip 90

    it 'set the tooltip value', ->
      expect($.fn.qtip).toHaveBeenCalledWith 'option', 'content.text', '1:30'
