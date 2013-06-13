describe 'VideoControl', ->
  beforeEach ->
    window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn false
    loadFixtures 'video.html'
    $('.video-controls').html ''

  describe 'constructor', ->

    it 'render the video controls', ->
      @control = new window.VideoControl(el: $('.video-controls'))
      expect($('.video-controls')).toContain
      ['.slider', 'ul.vcr', 'a.play', '.vidtime', '.add-fullscreen'].join(',')
      expect($('.video-controls').find('.vidtime')).toHaveText '0:00 / 0:00'

    it 'bind the playback button', ->
      @control = new window.VideoControl(el: $('.video-controls'))
      expect($('.video_control')).toHandleWith 'click', @control.togglePlayback

    describe 'when on a touch based device', ->
      beforeEach ->
        window.onTouchBasedDevice.andReturn true
        @control = new window.VideoControl(el: $('.video-controls'))

      it 'does not add the play class to video control', ->
        expect($('.video_control')).not.toHaveClass 'play'
        expect($('.video_control')).not.toHaveHtml 'Play'


    describe 'when on a non-touch based device', ->

      beforeEach ->
        @control = new window.VideoControl(el: $('.video-controls'))

      it 'add the play class to video control', ->
        expect($('.video_control')).toHaveClass 'play'
        expect($('.video_control')).toHaveHtml 'Play'

  describe 'play', ->

    beforeEach ->
      @control = new window.VideoControl(el: $('.video-controls'))
      @control.play()

    it 'switch playback button to play state', ->
      expect($('.video_control')).not.toHaveClass 'play'
      expect($('.video_control')).toHaveClass 'pause'
      expect($('.video_control')).toHaveHtml 'Pause'

  describe 'pause', ->

    beforeEach ->
      @control = new window.VideoControl(el: $('.video-controls'))
      @control.pause()

    it 'switch playback button to pause state', ->
      expect($('.video_control')).not.toHaveClass 'pause'
      expect($('.video_control')).toHaveClass 'play'
      expect($('.video_control')).toHaveHtml 'Play'

  describe 'togglePlayback', ->

    beforeEach ->
      @control = new window.VideoControl(el: $('.video-controls'))

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
