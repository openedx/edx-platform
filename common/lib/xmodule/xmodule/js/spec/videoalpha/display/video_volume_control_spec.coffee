describe 'VideoVolumeControlAlpha', ->
  beforeEach ->
    jasmine.stubVideoPlayerAlpha @
    $('.volume').remove()

  describe 'constructor', ->
    beforeEach ->
      spyOn($.fn, 'slider')
      @volumeControl = new VideoVolumeControlAlpha el: $('.secondary-controls')

    it 'initialize currentVolume to 100', ->
      expect(@volumeControl.currentVolume).toEqual 100

    it 'render the volume control', ->
      expect($('.secondary-controls').html()).toContain """
        <div class="volume">
          <a href="#"></a>
          <div class="volume-slider-container">
            <div class="volume-slider"></div>
          </div>
        </div>
      """

    it 'create the slider', ->
      expect($.fn.slider).toHaveBeenCalledWith
        orientation: "vertical"
        range: "min"
        min: 0
        max: 100
        value: 100
        change: @volumeControl.onChange
        slide: @volumeControl.onChange

    it 'bind the volume control', ->
      expect($('.volume>a')).toHandleWith 'click', @volumeControl.toggleMute

      expect($('.volume')).not.toHaveClass 'open'
      $('.volume').mouseenter()
      expect($('.volume')).toHaveClass 'open'
      $('.volume').mouseleave()
      expect($('.volume')).not.toHaveClass 'open'

  describe 'onChange', ->
    beforeEach ->
      spyOnEvent @volumeControl, 'volumeChange'
      @newVolume = undefined
      @volumeControl = new VideoVolumeControlAlpha el: $('.secondary-controls')
      $(@volumeControl).bind 'volumeChange', (event, volume) => @newVolume = volume

    describe 'when the new volume is more than 0', ->
      beforeEach ->
        @volumeControl.onChange undefined, value: 60

      it 'set the player volume', ->
        expect(@newVolume).toEqual 60

      it 'remote muted class', ->
        expect($('.volume')).not.toHaveClass 'muted'

    describe 'when the new volume is 0', ->
      beforeEach ->
        @volumeControl.onChange undefined, value: 0

      it 'set the player volume', ->
        expect(@newVolume).toEqual 0

      it 'add muted class', ->
        expect($('.volume')).toHaveClass 'muted'

  describe 'toggleMute', ->
    beforeEach ->
      @newVolume = undefined
      @volumeControl = new VideoVolumeControlAlpha el: $('.secondary-controls')
      $(@volumeControl).bind 'volumeChange', (event, volume) => @newVolume = volume

    describe 'when the current volume is more than 0', ->
      beforeEach ->
        @volumeControl.currentVolume = 60
        @volumeControl.toggleMute()

      it 'save the previous volume', ->
        expect(@volumeControl.previousVolume).toEqual 60

      it 'set the player volume', ->
        expect(@newVolume).toEqual 0

    describe 'when the current volume is 0', ->
      beforeEach ->
        @volumeControl.currentVolume = 0
        @volumeControl.previousVolume = 60
        @volumeControl.toggleMute()

      it 'set the player volume to previous volume', ->
        expect(@newVolume).toEqual 60
