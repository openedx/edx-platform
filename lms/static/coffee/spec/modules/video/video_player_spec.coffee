describe 'VideoPlayer', ->
  beforeEach ->
    jasmine.stubVideoPlayer @

  afterEach ->
    YT.Player = undefined

  describe 'constructor', ->
    beforeEach ->
      spyOn window, 'VideoControl'
      spyOn YT, 'Player'
      $.fn.qtip.andCallFake ->
        $(this).data('qtip', true)
      $('.video').append $('<div class="hide-subtitles" />')
      @player = new VideoPlayer @video

    it 'instanticate current time to zero', ->
      expect(@player.currentTime).toEqual 0

    it 'set the element', ->
      expect(@player.element).toBe '#video_example'

    it 'create video control', ->
      expect(window.VideoControl).toHaveBeenCalledWith @player

    it 'create video caption', ->
      expect(window.VideoCaption).toHaveBeenCalledWith @player, 'def456'

    it 'create video speed control', ->
      expect(window.VideoSpeedControl).toHaveBeenCalledWith @player, ['0.75', '1.0']

    it 'create video progress slider', ->
      expect(window.VideoProgressSlider).toHaveBeenCalledWith @player

    it 'create Youtube player', ->
      expect(YT.Player).toHaveBeenCalledWith 'example'
        playerVars:
          controls: 0
          wmode: 'transparent'
          rel: 0
          showinfo: 0
          enablejsapi: 1
        videoId: 'def456'
        events:
          onReady: @player.onReady
          onStateChange: @player.onStateChange

    it 'bind to seek event', ->
      expect($(@player)).toHandleWith 'seek', @player.onSeek

    it 'bind to updatePlayTime event', ->
      expect($(@player)).toHandleWith 'updatePlayTime', @player.onUpdatePlayTime

    it 'bidn to speedChange event', ->
      expect($(@player)).toHandleWith 'speedChange', @player.onSpeedChange

    it 'bind to play event', ->
      expect($(@player)).toHandleWith 'play', @player.onPlay

    it 'bind to paused event', ->
      expect($(@player)).toHandleWith 'pause', @player.onPause

    it 'bind to ended event', ->
      expect($(@player)).toHandleWith 'ended', @player.onPause

    it 'bind to key press', ->
      expect($(document)).toHandleWith 'keyup', @player.bindExitFullScreen

    it 'bind to fullscreen switching button', ->
      expect($('.add-fullscreen')).toHandleWith 'click', @player.toggleFullScreen

    describe 'when not on a touch based device', ->
      it 'add the tooltip to fullscreen and subtitle button', ->
        expect($('.add-fullscreen')).toHaveData 'qtip'
        expect($('.hide-subtitles')).toHaveData 'qtip'

  describe 'onReady', ->
    beforeEach ->
      @video.embed()
      @player = @video.player
      spyOnEvent @player, 'ready'
      spyOnEvent @player, 'updatePlayTime'
      @player.onReady()

    it 'reset the progress to zero', ->
      expect('updatePlayTime').toHaveBeenTriggeredOn @player

    it 'trigger ready event on the player', ->
      expect('ready').toHaveBeenTriggeredOn @player

    describe 'when not on a touch based device', ->
      beforeEach ->
        spyOn(window, 'onTouchBasedDevice').andReturn false
        spyOn @player, 'play'
        @player.onReady()

      it 'autoplay the first video', ->
        expect(@player.play).toHaveBeenCalled()

    describe 'when on a touch based device', ->
      beforeEach ->
        spyOn(window, 'onTouchBasedDevice').andReturn true
        spyOn @player, 'play'
        @player.onReady()

      it 'does not autoplay the first video', ->
        expect(@player.play).not.toHaveBeenCalled()

  describe 'onStateChange', ->
    beforeEach ->
      @player = new VideoPlayer @video

    describe 'when the video is playing', ->
      beforeEach ->
        spyOnEvent @player, 'play'
        @player.onStateChange data: YT.PlayerState.PLAYING

      it 'trigger play event', ->
        expect('play').toHaveBeenTriggeredOn @player

    describe 'when the video is paused', ->
      beforeEach ->
        spyOnEvent @player, 'pause'
        @player.onStateChange data: YT.PlayerState.PAUSED

      it 'trigger pause event', ->
        expect('pause').toHaveBeenTriggeredOn @player

    describe 'when the video is unstarted', ->
      beforeEach ->
        spyOnEvent @player, 'pause'
        @player.onStateChange data: YT.PlayerState.UNSTARTED

      it 'trigger pause event', ->
        expect('pause').toHaveBeenTriggeredOn @player

    describe 'when the video is ended', ->
      beforeEach ->
        spyOnEvent @player, 'ended'
        @player.onStateChange data: YT.PlayerState.ENDED

      it 'trigger ended event', ->
        expect('ended').toHaveBeenTriggeredOn @player

  describe 'onPlay', ->
    beforeEach ->
      @player = new VideoPlayer @video
      @anotherPlayer = jasmine.createSpyObj 'AnotherPlayer', ['pauseVideo']
      window.player = @anotherPlayer
      spyOn Logger, 'log'
      spyOn(window, 'setInterval').andReturn 100
      @player.player.getVideoEmbedCode.andReturn 'embedCode'
      @player.onPlay()

    it 'log the play_video event', ->
      expect(Logger.log).toHaveBeenCalledWith 'play_video', id: @player.currentTime, code: 'embedCode'

    it 'pause other video player', ->
      expect(@anotherPlayer.pauseVideo).toHaveBeenCalled()

    it 'set current video player as active player', ->
      expect(window.player).toEqual @player.player

    it 'set update interval', ->
      expect(window.setInterval).toHaveBeenCalledWith @player.update, 200
      expect(@player.player.interval).toEqual 100

  describe 'onPause', ->
    beforeEach ->
      @player = new VideoPlayer @video
      window.player = @player.player
      spyOn Logger, 'log'
      spyOn window, 'clearInterval'
      @player.player.interval = 100
      @player.player.getVideoEmbedCode.andReturn 'embedCode'
      @player.onPause()

    it 'log the pause_video event', ->
      expect(Logger.log).toHaveBeenCalledWith 'pause_video', id: @player.currentTime, code: 'embedCode'

    it 'set current video player as inactive', ->
      expect(window.player).toBeNull()

    it 'clear update interval', ->
      expect(window.clearInterval).toHaveBeenCalledWith 100
      expect(@player.player.interval).toBeNull()

  describe 'onSeek', ->
    beforeEach ->
      @player = new VideoPlayer @video
      spyOn window, 'clearInterval'
      @player.player.interval = 100
      @player.onSeek {}, 60

    it 'seek the player', ->
      expect(@player.player.seekTo).toHaveBeenCalledWith 60, true

    describe 'when the player is playing', ->
      beforeEach ->
        @player.player.getPlayerState.andReturn YT.PlayerState.PLAYING
        @player.onSeek {}, 60

      it 'reset the update interval', ->
        expect(window.clearInterval).toHaveBeenCalledWith 100

    describe 'when the player is not playing', ->
      beforeEach ->
        @player.player.getPlayerState.andReturn YT.PlayerState.PAUSED
        spyOnEvent @player, 'updatePlayTime'
        @player.onSeek {}, 60

      it 'set the current time', ->
        expect(@player.currentTime).toEqual 60

      it 'trigger updatePlayTime event', ->
        expect('updatePlayTime').toHaveBeenTriggeredOn @player

  describe 'onSpeedChange', ->
    beforeEach ->
      @player = new VideoPlayer @video
      @player.currentTime = 60
      spyOn(@video, 'setSpeed').andCallThrough()

    describe 'always', ->
      beforeEach ->
        @player.onSpeedChange {}, '0.75'

      it 'convert the current time to the new speed', ->
        expect(@player.currentTime).toEqual '80.000'

      it 'set video speed to the new speed', ->
        expect(@video.setSpeed).toHaveBeenCalledWith '0.75'

    describe 'when the video is playing', ->
      beforeEach ->
        @player.player.getPlayerState.andReturn YT.PlayerState.PLAYING
        spyOnEvent @player, 'updatePlayTime'
        @player.onSpeedChange {}, '0.75'

      it 'load the video', ->
        expect(@player.player.loadVideoById).toHaveBeenCalledWith 'abc123', '80.000'

      it 'trigger updatePlayTime event', ->
        expect('updatePlayTime').toHaveBeenTriggeredOn @player

    describe 'when the video is not playing', ->
      beforeEach ->
        @player.player.getPlayerState.andReturn YT.PlayerState.PAUSED
        spyOnEvent @player, 'updatePlayTime'
        @player.onSpeedChange {}, '0.75'

      it 'cue the video', ->
        expect(@player.player.cueVideoById).toHaveBeenCalledWith 'abc123', '80.000'

      it 'trigger updatePlayTime event', ->
        expect('updatePlayTime').toHaveBeenTriggeredOn @player

  describe 'update', ->
    beforeEach ->
      @player = new VideoPlayer @video
      spyOnEvent @player, 'updatePlayTime'

    describe 'when the current time is unavailable from the player', ->
      beforeEach ->
        @player.player.getCurrentTime.andReturn undefined
        @player.update()

      it 'does not trigger updatePlayTime event', ->
        expect('updatePlayTime').not.toHaveBeenTriggeredOn @player

    describe 'when the current time is available from the player', ->
      beforeEach ->
        @player.player.getCurrentTime.andReturn 60
        @player.update()

      it 'trigger updatePlayTime event', ->
        expect('updatePlayTime').toHaveBeenTriggeredOn @player

  describe 'onUpdatePlaytime', ->
    beforeEach ->
      @player = new VideoPlayer @video
      spyOn(@video, 'getDuration').andReturn 1800
      @player.onUpdatePlayTime {}, 60

    it 'update the video playback time', ->
      expect($('.vidtime')).toHaveHtml '1:00 / 30:00'

  describe 'toggleFullScreen', ->
    beforeEach ->
      @player = new VideoPlayer @video

    describe 'when the video player is not full screen', ->
      beforeEach ->
        @player.element.removeClass 'fullscreen'
        spyOnEvent @player, 'resize'
        @player.toggleFullScreen(jQuery.Event("click"))

      it 'replace the full screen button tooltip', ->
        expect($('.add-fullscreen')).toHaveAttr 'title', 'Exit fill browser'

      it 'add a new exit from fullscreen button', ->
        expect(@player.element).toContain 'a.exit'

      it 'add the fullscreen class', ->
        expect(@player.element).toHaveClass 'fullscreen'

      it 'trigger resize event', ->
        expect('resize').toHaveBeenTriggeredOn @player

    describe 'when the video player already full screen', ->
      beforeEach ->
        @player.element.addClass 'fullscreen'
        spyOnEvent @player, 'resize'
        @player.toggleFullScreen(jQuery.Event("click"))

      it 'replace the full screen button tooltip', ->
        expect($('.add-fullscreen')).toHaveAttr 'title', 'Fill browser'

      it 'remove exit full screen button', ->
        expect(@player.element).not.toContain 'a.exit'

      it 'remove the fullscreen class', ->
        expect(@player.element).not.toHaveClass 'fullscreen'

      it 'trigger resize event', ->
        expect('resize').toHaveBeenTriggeredOn @player

  describe 'play', ->
    beforeEach ->
      @player = new VideoPlayer @video

    describe 'when the player is not ready', ->
      beforeEach ->
        @player.player.playVideo = undefined
        @player.play()

      it 'does nothing', ->
        expect(@player.player.playVideo).toBeUndefined()

    describe 'when the player is ready', ->
      beforeEach ->
        @player.player.playVideo.andReturn true
        @player.play()

      it 'delegate to the Youtube player', ->
        expect(@player.player.playVideo).toHaveBeenCalled()

  describe 'isPlaying', ->
    beforeEach ->
      @player = new VideoPlayer @video

    describe 'when the video is playing', ->
      beforeEach ->
        @player.player.getPlayerState.andReturn YT.PlayerState.PLAYING

      it 'return true', ->
        expect(@player.isPlaying()).toBeTruthy()

    describe 'when the video is not playing', ->
      beforeEach ->
        @player.player.getPlayerState.andReturn YT.PlayerState.PAUSED

      it 'return false', ->
        expect(@player.isPlaying()).toBeFalsy()

  describe 'pause', ->
    beforeEach ->
      @player = new VideoPlayer @video
      @player.pause()

    it 'delegate to the Youtube player', ->
      expect(@player.player.pauseVideo).toHaveBeenCalled()

  describe 'duration', ->
    beforeEach ->
      @player = new VideoPlayer @video
      spyOn @video, 'getDuration'
      @player.duration()

    it 'delegate to the video', ->
      expect(@video.getDuration).toHaveBeenCalled()

  describe 'currentSpeed', ->
    beforeEach ->
      @player = new VideoPlayer @video
      @video.speed = '3.0'

    it 'delegate to the video', ->
      expect(@player.currentSpeed()).toEqual '3.0'

  describe 'volume', ->
    beforeEach ->
      @player = new VideoPlayer @video
      @player.player.getVolume.andReturn 42

    describe 'without value', ->
      it 'return current volume', ->
        expect(@player.volume()).toEqual 42

    describe 'with value', ->
      it 'set player volume', ->
        @player.volume(60)
        expect(@player.player.setVolume).toHaveBeenCalledWith(60)
