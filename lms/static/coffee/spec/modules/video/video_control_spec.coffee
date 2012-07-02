describe 'VideoControl', ->
  beforeEach ->
    jasmine.stubVideoPlayer @
    $('.video-controls').html ''

  describe 'constructor', ->
    it 'render the video controls', ->
      new VideoControl(el: $('.video-controls'))
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

    it 'bind the playback button', ->
      control = new VideoControl(el: $('.video-controls'))
      expect($('.video_control')).toHandleWith 'click', control.togglePlayback

    describe 'when on a touch based device', ->
      beforeEach ->
        spyOn(window, 'onTouchBasedDevice').andReturn true

      it 'does not add the play class to video control', ->
        new VideoControl(el: $('.video-controls'))
        expect($('.video_control')).not.toHaveClass 'play'
        expect($('.video_control')).not.toHaveHtml 'Play'


    describe 'when on a non-touch based device', ->
      beforeEach ->
        spyOn(window, 'onTouchBasedDevice').andReturn false

      it 'add the play class to video control', ->
        new VideoControl(el: $('.video-controls'))
        expect($('.video_control')).toHaveClass 'play'
        expect($('.video_control')).toHaveHtml 'Play'

  describe 'play', ->
    beforeEach ->
      @control = new VideoControl(el: $('.video-controls'))
      @control.play()

    it 'switch playback button to play state', ->
      expect($('.video_control')).not.toHaveClass 'play'
      expect($('.video_control')).toHaveClass 'pause'
      expect($('.video_control')).toHaveHtml 'Pause'

  describe 'pause', ->
    beforeEach ->
      @control = new VideoControl(el: $('.video-controls'))
      @control.pause()

    it 'switch playback button to pause state', ->
      expect($('.video_control')).not.toHaveClass 'pause'
      expect($('.video_control')).toHaveClass 'play'
      expect($('.video_control')).toHaveHtml 'Play'

  describe 'togglePlayback', ->
    beforeEach ->
      @control = new VideoControl(el: $('.video-controls'))

    describe 'when the control does not have play or pause class', ->
      beforeEach ->
        $('.video_control').removeClass('play').removeClass('pause')

      describe 'when the video is playing', ->
        beforeEach ->
          $('.video_control').addClass('play')
          spyOnEvent @control, 'pause'
          @control.togglePlayback jQuery.Event('click')

        it 'does not trigger the pause event', ->
          expect('pause').not.toHaveBeenTriggeredOn @control

      describe 'when the video is paused', ->
        beforeEach ->
          $('.video_control').addClass('pause')
          spyOnEvent @control, 'play'
          @control.togglePlayback jQuery.Event('click')

        it 'does not trigger the play event', ->
          expect('play').not.toHaveBeenTriggeredOn @control

      describe 'when the video is playing', ->
        beforeEach ->
          spyOnEvent @control, 'pause'
          $('.video_control').addClass 'pause'
          @control.togglePlayback jQuery.Event('click')

        it 'trigger the pause event', ->
          expect('pause').toHaveBeenTriggeredOn @control

      describe 'when the video is paused', ->
        beforeEach ->
          spyOnEvent @control, 'play'
          $('.video_control').addClass 'play'
          @control.togglePlayback jQuery.Event('click')

        it 'trigger the play event', ->
          expect('play').toHaveBeenTriggeredOn @control
