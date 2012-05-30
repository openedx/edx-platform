describe 'VideoProgressSlider', ->
  beforeEach ->
    @player = jasmine.stubVideoPlayer @

  describe 'constructor', ->
    beforeEach ->
      spyOn($.fn, 'slider').andCallThrough()
      @slider = new VideoProgressSlider @player

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

    it 'bind player events', ->
      expect($(@player)).toHandleWith 'updatePlayTime', @slider.onUpdatePlayTime

  describe 'onReady', ->
    beforeEach ->
      spyOn(@player, 'duration').andReturn 120
      @slider = new VideoProgressSlider @player
      @slider.onReady()

    it 'set the max value to the length of video', ->
      expect(@slider.slider.slider('option', 'max')).toEqual 120

  describe 'onUpdatePlayTime', ->
    beforeEach ->
      @slider = new VideoProgressSlider @player
      spyOn(@player, 'duration').andReturn 120
      spyOn($.fn, 'slider').andCallThrough()

    describe 'when frozen', ->
      beforeEach ->
        @slider.frozen = true
        @slider.onUpdatePlayTime {}, 20

      it 'does not update the slider', ->
        expect($.fn.slider).not.toHaveBeenCalled()

    describe 'when not frozen', ->
      beforeEach ->
        @slider.frozen = false
        @slider.onUpdatePlayTime {}, 20

      it 'update the max value of the slider', ->
        expect($.fn.slider).toHaveBeenCalledWith 'option', 'max', 120

      it 'update current value of the slider', ->
        expect($.fn.slider).toHaveBeenCalledWith 'value', 20

  describe 'onSlide', ->
    beforeEach ->
      @slider = new VideoProgressSlider @player
      @time = null
      $(@player).bind 'seek', (event, time) => @time = time
      spyOnEvent @player, 'seek'
      @slider.onSlide {}, value: 20

    it 'freeze the slider', ->
      expect(@slider.frozen).toBeTruthy()

    it 'update the tooltip', ->
      expect($.fn.qtip).toHaveBeenCalled()

    it 'trigger seek event', ->
      expect('seek').toHaveBeenTriggeredOn @player
      expect(@time).toEqual 20

  describe 'onChange', ->
    beforeEach ->
      @slider = new VideoProgressSlider @player
      @slider.onChange {}, value: 20

    it 'update the tooltip', ->
      expect($.fn.qtip).toHaveBeenCalled()

  describe 'onStop', ->
    beforeEach ->
      @slider = new VideoProgressSlider @player
      @time = null
      $(@player).bind 'seek', (event, time) => @time = time
      spyOnEvent @player, 'seek'
      spyOn(window, 'setTimeout')
      @slider.onStop {}, value: 20

    it 'freeze the slider', ->
      expect(@slider.frozen).toBeTruthy()

    it 'trigger seek event', ->
      expect('seek').toHaveBeenTriggeredOn @player
      expect(@time).toEqual 20

    it 'set timeout to unfreeze the slider', ->
      expect(window.setTimeout).toHaveBeenCalledWith jasmine.any(Function), 200
      window.setTimeout.mostRecentCall.args[0]()
      expect(@slider.frozen).toBeFalsy()

  describe 'updateTooltip', ->
    beforeEach ->
      @slider = new VideoProgressSlider @player
      @slider.updateTooltip 90

    it 'set the tooltip value', ->
      expect($.fn.qtip).toHaveBeenCalledWith 'option', 'content.text', '1:30'
