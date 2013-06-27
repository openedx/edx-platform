describe 'VideoAlpha HTML5Video', ->
  playbackRates = [0.75, 1.0, 1.25, 1.5]
  STATUS = window.YT.PlayerState
  playerVars =
    controls: 0
    wmode: 'transparent'
    rel: 0
    showinfo: 0
    enablejsapi: 1
    modestbranding: 1
    html5: 1
  file = window.location.href.replace(/\/common(.*)$/, '') + '/test_root/data/videoalpha/gizmo'
  html5Sources =
    mp4: "#{file}.mp4"
    webm: "#{file}.webm"
    ogg: "#{file}.ogv"
  onReady = jasmine.createSpy 'onReady'
  onStateChange = jasmine.createSpy 'onStateChange'

  beforeEach ->
    loadFixtures 'videoalpha_html5.html'
    @el = $('#example').find('.video')
    @player = new window.HTML5Video.Player @el,
      playerVars: playerVars,
      videoSources: html5Sources,
      events:
        onReady: onReady
        onStateChange: onStateChange

    @videoEl = @el.find('.video-player video').get(0)

  it 'PlayerState', ->
    expect(HTML5Video.PlayerState).toEqual STATUS

  describe 'constructor', ->
    it 'create an html5 video element', ->
      expect(@el.find('.video-player div')).toContain 'video'

    it 'check if sources are created in correct way', ->
      sources = $(@videoEl).find('source')
      videoTypes = []
      videoSources = []
      $.each html5Sources, (index, source) ->
        videoTypes.push index
        videoSources.push source
      $.each sources, (index, source) ->
        s = $(source)
        expect($.inArray(s.attr('src'), videoSources)).not.toEqual -1
        expect($.inArray(s.attr('type').replace('video/', ''), videoTypes))
          .not.toEqual -1

    it 'check if click event is handled on the player', ->
        expect(@videoEl).toHandle 'click'

  # NOTE: According to
  #
  # https://github.com/ariya/phantomjs/wiki/Supported-Web-Standards#unsupported-features
  #
  # Video and Audio (due to the nature of PhantomJS) are not supported. After discussion
  # with William Daly, some tests are disabled (Jenkins uses phantomjs for running tests
  # and those tests fail).
  #
  # During code review, please enable the test below (change "xdescribe" to "describe"
  # to enable the test).
  xdescribe 'events:', ->

    beforeEach ->
      spyOn(@player, 'callStateChangeCallback').andCallThrough()

    describe 'click', ->
      describe 'when player is paused', ->
        beforeEach ->
          spyOn(@videoEl, 'play').andCallThrough()
          @player.playerState = STATUS.PAUSED
          $(@videoEl).trigger('click')

        it 'native play event was called', ->
          expect(@videoEl.play).toHaveBeenCalled()

        it 'player state was changed', ->
          expect(@player.playerState).toBe STATUS.PLAYING

        it 'callback was called', ->
          expect(@player.callStateChangeCallback).toHaveBeenCalled()

      describe 'when player is played', ->

        beforeEach ->
          spyOn(@videoEl, 'pause').andCallThrough()
          @player.playerState = STATUS.PLAYING
          $(@videoEl).trigger('click')

        it 'native pause event was called', ->
          expect(@videoEl.pause).toHaveBeenCalled()

        it 'player state was changed', ->
          expect(@player.playerState).toBe STATUS.PAUSED

        it 'callback was called', ->
          expect(@player.callStateChangeCallback).toHaveBeenCalled()

    describe 'play', ->

      beforeEach ->
        spyOn(@videoEl, 'play').andCallThrough()
        @player.playerState = STATUS.PAUSED
        @videoEl.play()

      it 'native event was called', ->
        expect(@videoEl.play).toHaveBeenCalled()

      it 'player state was changed', ->
        waitsFor ( ->
          @player.playerState != HTML5Video.PlayerState.PAUSED
        ), 'Player state should be changed', 1000

        runs ->
          expect(@player.playerState).toBe STATUS.PLAYING

      it 'callback was called', ->
        waitsFor ( ->
          @player.playerState != STATUS.PAUSED
        ), 'Player state should be changed', 1000

        runs ->
          expect(@player.callStateChangeCallback).toHaveBeenCalled()

    describe 'pause', ->

      beforeEach ->
        spyOn(@videoEl, 'pause').andCallThrough()
        @videoEl.play()
        @videoEl.pause()

      it 'native event was called', ->
        expect(@videoEl.pause).toHaveBeenCalled()

      it 'player state was changed', ->
        waitsFor ( ->
          @player.playerState != STATUS.UNSTARTED
        ), 'Player state should be changed', 1000

        runs ->
          expect(@player.playerState).toBe STATUS.PAUSED

      it 'callback was called', ->
        waitsFor ( ->
          @player.playerState != HTML5Video.PlayerState.UNSTARTED
        ), 'Player state should be changed', 1000

        runs ->
          expect(@player.callStateChangeCallback).toHaveBeenCalled()

    describe 'canplay', ->

      beforeEach ->
        waitsFor ( ->
          @player.playerState != STATUS.UNSTARTED
        ), 'Video cannot be played', 1000

      it 'player state was changed', ->
        runs ->
          expect(@player.playerState).toBe STATUS.PAUSED

      it 'end property was defined', ->
        runs ->
          expect(@player.end).not.toBeNull()

      it 'start position was defined', ->
        runs ->
          expect(@videoEl.currentTime).toBe(@player.start)

      it 'callback was called', ->
        runs ->
          expect(@player.config.events.onReady).toHaveBeenCalled()

    describe 'ended', ->
      beforeEach ->
        waitsFor ( ->
          @player.playerState != STATUS.UNSTARTED
        ), 'Video cannot be played', 1000

      it 'player state was changed', ->
        runs ->
          jasmine.fireEvent @videoEl, "ended"
          expect(@player.playerState).toBe STATUS.ENDED

      it 'callback was called', ->
          jasmine.fireEvent @videoEl, "ended"
          expect(@player.callStateChangeCallback).toHaveBeenCalled()

    describe 'timeupdate', ->

      beforeEach ->
        spyOn(@videoEl, 'pause').andCallThrough()
        waitsFor ( ->
          @player.playerState != STATUS.UNSTARTED
        ), 'Video cannot be played', 1000

      it 'player should be paused', ->
        runs ->
          @player.end = 3
          @videoEl.currentTime = 5
          jasmine.fireEvent @videoEl, "timeupdate"
          expect(@videoEl.pause).toHaveBeenCalled()

      it 'end param should be re-defined', ->
        runs ->
          @player.end = 3
          @videoEl.currentTime = 5
          jasmine.fireEvent @videoEl, "timeupdate"
          expect(@player.end).toBe @videoEl.duration

  # NOTE: According to
  #
  # https://github.com/ariya/phantomjs/wiki/Supported-Web-Standards#unsupported-features
  #
  # Video and Audio (due to the nature of PhantomJS) are not supported. After discussion
  # with William Daly, some tests are disabled (Jenkins uses phantomjs for running tests
  # and those tests fail).
  #
  # During code review, please enable the test below (change "xdescribe" to "describe"
  # to enable the test).
  xdescribe 'methods:', ->

    beforeEach ->
      waitsFor ( ->
        @volume = @videoEl.volume
        @seek = @videoEl.currentTime
        @player.playerState == STATUS.PAUSED
      ), 'Video cannot be played', 1000


    it 'pauseVideo', ->
      spyOn(@videoEl, 'pause').andCallThrough()
      @player.pauseVideo()
      expect(@videoEl.pause).toHaveBeenCalled()

    describe 'seekTo', ->

      it 'set new correct value', ->
        runs ->
          @player.seekTo(2)
          expect(@videoEl.currentTime).toBe 2

      it 'set new inccorrect values', ->
        runs ->
          @player.seekTo(-50)
          expect(@videoEl.currentTime).toBe @seek
          @player.seekTo('5')
          expect(@videoEl.currentTime).toBe @seek
          @player.seekTo(500000)
          expect(@videoEl.currentTime).toBe @seek

    describe 'setVolume', ->

      it 'set new correct value', ->
        runs ->
          @player.setVolume(50)
          expect(@videoEl.volume).toBe 50*0.01

      it 'set new inccorrect values', ->
        runs ->
          @player.setVolume(-50)
          expect(@videoEl.volume).toBe @volume
          @player.setVolume('5')
          expect(@videoEl.volume).toBe @volume
          @player.setVolume(500000)
          expect(@videoEl.volume).toBe @volume

    it 'getCurrentTime', ->
      runs ->
        @videoEl.currentTime = 3
        expect(@player.getCurrentTime()).toBe @videoEl.currentTime

    it 'playVideo', ->
      runs ->
        spyOn(@videoEl, 'play').andCallThrough()
        @player.playVideo()
        expect(@videoEl.play).toHaveBeenCalled()

    it 'getPlayerState', ->
      runs ->
        @player.playerState = STATUS.PLAYING
        expect(@player.getPlayerState()).toBe STATUS.PLAYING
        @player.playerState = STATUS.ENDED
        expect(@player.getPlayerState()).toBe STATUS.ENDED

    it 'getVolume', ->
      runs ->
        @volume = @videoEl.volume = 0.5
        expect(@player.getVolume()).toBe @volume

    it 'getDuration', ->
      runs ->
        @duration = @videoEl.duration
        expect(@player.getDuration()).toBe @duration

    describe 'setPlaybackRate', ->
      it 'set a correct value', ->
        @playbackRate = 1.5
        @player.setPlaybackRate @playbackRate
        expect(@videoEl.playbackRate).toBe @playbackRate

      it 'set NaN value', ->
        @playbackRate = NaN
        @player.setPlaybackRate @playbackRate
        expect(@videoEl.playbackRate).toBe 1.0

    it 'getAvailablePlaybackRates', ->
      expect(@player.getAvailablePlaybackRates()).toEqual playbackRates
