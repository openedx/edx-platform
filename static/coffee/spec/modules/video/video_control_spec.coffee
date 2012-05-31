describe 'VideoControl', ->
  beforeEach ->
    @player = jasmine.stubVideoPlayer @
    $('.video-controls').html ''

  describe 'constructor', ->
    it 'render the video controls', ->
      new VideoControl @player
      expect($('.video-controls').html()).toContain '''
        <div class="slider"></div>
        <div>
          <ul class="vcr">
            <li><a class="video_control play" href="#">Play</a></li>
            <li>
              <div class="vidtime">0:00 / 0:00</div>
            </li>
          </ul>
          <div class="secondary-controls">
            <a href="#" class="add-fullscreen" title="Fill browser">Fill Browser</a>
          </div>
        </div>
      '''

    it 'bind player events', ->
      control = new VideoControl @player
      expect($(@player)).toHandleWith 'play', control.onPlay
      expect($(@player)).toHandleWith 'pause', control.onPause
      expect($(@player)).toHandleWith 'ended', control.onPause

    it 'bind the playback button', ->
      control = new VideoControl @player
      expect($('.video_control')).toHandleWith 'click', control.togglePlayback

    describe 'when on a touch based device', ->
      beforeEach ->
        spyOn(window, 'onTouchBasedDevice').andReturn true

      it 'does not add the play class to video control', ->
        new VideoControl @player
        expect($('.video_control')).not.toHaveClass 'play'
        expect($('.video_control')).not.toHaveHtml 'Play'


    describe 'when on a non-touch based device', ->
      beforeEach ->
        spyOn(window, 'onTouchBasedDevice').andReturn false

      it 'add the play class to video control', ->
        new VideoControl @player
        expect($('.video_control')).toHaveClass 'play'
        expect($('.video_control')).toHaveHtml 'Play'

  describe 'onPlay', ->
    beforeEach ->
      @control = new VideoControl @player
      @control.onPlay()

    it 'switch playback button to play state', ->
      expect($('.video_control')).not.toHaveClass 'play'
      expect($('.video_control')).toHaveClass 'pause'
      expect($('.video_control')).toHaveHtml 'Pause'

  describe 'onPause', ->
    beforeEach ->
      @control = new VideoControl @player
      @control.onPause()

    it 'switch playback button to pause state', ->
      expect($('.video_control')).not.toHaveClass 'pause'
      expect($('.video_control')).toHaveClass 'play'
      expect($('.video_control')).toHaveHtml 'Play'

  describe 'togglePlayback', ->
    beforeEach ->
      @control = new VideoControl @player

    describe 'when the control does not have play or pause class', ->
      beforeEach ->
        $('.video_control').removeClass('play').removeClass('pause')

      describe 'when the video is playing', ->
        beforeEach ->
          spyOn(@player, 'isPlaying').andReturn true
          spyOnEvent @player, 'pause'
          @control.togglePlayback jQuery.Event('click')

        it 'does not trigger the pause event', ->
          expect('pause').not.toHaveBeenTriggeredOn @player

      describe 'when the video is paused', ->
        beforeEach ->
          spyOn(@player, 'isPlaying').andReturn false
          spyOnEvent @player, 'play'
          @control.togglePlayback jQuery.Event('click')

        it 'does not trigger the play event', ->
          expect('play').not.toHaveBeenTriggeredOn @player

    for className in ['play', 'pause']
      describe "when the control has #{className} class", ->
        beforeEach ->
          $('.video_control').addClass className

        describe 'when the video is playing', ->
          beforeEach ->
            spyOn(@player, 'isPlaying').andReturn true
            spyOnEvent @player, 'pause'
            @control.togglePlayback jQuery.Event('click')

          it 'trigger the pause event', ->
            expect('pause').toHaveBeenTriggeredOn @player

        describe 'when the video is paused', ->
          beforeEach ->
            spyOn(@player, 'isPlaying').andReturn false
            spyOnEvent @player, 'play'
            @control.togglePlayback jQuery.Event('click')

          it 'trigger the play event', ->
            expect('play').toHaveBeenTriggeredOn @player
