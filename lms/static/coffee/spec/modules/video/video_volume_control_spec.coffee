describe 'VideoVolumeControl', ->
  beforeEach ->
    @player = jasmine.stubVideoPlayer @
    $('.volume').remove()

  describe 'constructor', ->
    beforeEach ->
      spyOn($.fn, 'slider')
      @volumeControl = new VideoVolumeControl @player

    it 'initialize previousVolume to 100', ->
      expect(@volumeControl.previousVolume).toEqual 100

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
      expect($(@player)).toHandleWith 'ready', @volumeControl.onReady
      expect($('.volume>a')).toHandleWith 'click', @volumeControl.toggleMute

      expect($('.volume')).not.toHaveClass 'open'
      $('.volume').mouseenter()
      expect($('.volume')).toHaveClass 'open'
      $('.volume').mouseleave()
      expect($('.volume')).not.toHaveClass 'open'

  describe 'onReady', ->
    beforeEach ->
      @volumeControl = new VideoVolumeControl @player
      spyOn $.fn, 'slider'
      spyOn(@player, 'volume').andReturn 60
      @volumeControl.onReady()

    it 'set the max value of the slider', ->
      expect($.fn.slider).toHaveBeenCalledWith 'option', 'max', 60

  describe 'onChange', ->
    beforeEach ->
      spyOn @player, 'volume'
      @volumeControl = new VideoVolumeControl @player

    describe 'when the new volume is more than 0', ->
      beforeEach ->
        @volumeControl.onChange undefined, value: 60

      it 'set the player volume', ->
        expect(@player.volume).toHaveBeenCalledWith 60

      it 'remote muted class', ->
        expect($('.volume')).not.toHaveClass 'muted'

    describe 'when the new volume is 0', ->
      beforeEach ->
        @volumeControl.onChange undefined, value: 0

      it 'set the player volume', ->
        expect(@player.volume).toHaveBeenCalledWith 0

      it 'add muted class', ->
        expect($('.volume')).toHaveClass 'muted'

  describe 'toggleMute', ->
    beforeEach ->
      spyOn @player, 'volume'
      @volumeControl = new VideoVolumeControl @player

    describe 'when the current volume is more than 0', ->
      beforeEach ->
        @player.volume.andReturn 60
        @volumeControl.toggleMute()

      it 'save the previous volume', ->
        expect(@volumeControl.previousVolume).toEqual 60

      it 'set the player volume', ->
        expect(@player.volume).toHaveBeenCalledWith 0

    describe 'when the current volume is 0', ->
      beforeEach ->
        @player.volume.andReturn 0
        @volumeControl.previousVolume = 60
        @volumeControl.toggleMute()

      it 'set the player volume to previous volume', ->
        expect(@player.volume).toHaveBeenCalledWith 60
