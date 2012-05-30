describe 'VideoControl', ->
  beforeEach ->
    @player = jasmine.stubVideoPlayer @

  describe 'constructor', ->
    beforeEach ->
      @control = new VideoControl @player

    it 'render the video controls', ->
      expect($('.video-controls').html()).toContain '''
        <div class="slider"></div>
        <div>
          <ul class="vcr">
            <li><a class="video_control play">Play</a></li>
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
      expect($(@player)).toHandleWith 'play', @control.onPlay
      expect($(@player)).toHandleWith 'pause', @control.onPause
      expect($(@player)).toHandleWith 'ended', @control.onPause

    it 'bind the playback button', ->
      expect($('.video_control')).toHandleWith 'click', @control.togglePlayback

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
