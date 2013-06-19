describe 'VideoPlayerAlpha', ->
  playerVars =
    controls: 0
    wmode: 'transparent'
    rel: 0
    showinfo: 0
    enablejsapi: 1
    modestbranding: 1
    html5: 1

  beforeEach ->
    window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn false
    # It tries to call methods of VideoProgressSlider on Spy
    for part in ['VideoCaptionAlpha', 'VideoSpeedControlAlpha', 'VideoVolumeControlAlpha', 'VideoProgressSliderAlpha', 'VideoControlAlpha']
      spyOn(window[part].prototype, 'initialize').andCallThrough()


  afterEach ->
    YT.Player = undefined

  describe 'constructor', ->
    beforeEach ->
      $.fn.qtip.andCallFake ->
        $(this).data('qtip', true)

    describe 'always', ->
      beforeEach ->
        jasmine.stubVideoPlayerAlpha @, [], false
        $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
        @player = new VideoPlayerAlpha video: @video

      it 'instanticate current time to zero', ->
        expect(@player.currentTime).toEqual 0

      it 'set the element', ->
        expect(@player.el).toHaveId 'video_id'

      it 'create video control', ->
        expect(window.VideoControlAlpha.prototype.initialize).toHaveBeenCalled()
        expect(@player.control).toBeDefined()
        expect(@player.control.el).toBe $('.video-controls', @player.el)

      it 'create video caption', ->
        expect(window.VideoCaptionAlpha.prototype.initialize).toHaveBeenCalled()
        expect(@player.caption).toBeDefined()
        expect(@player.caption.el).toBe @player.el
        expect(@player.caption.youtubeId).toEqual 'normalSpeedYoutubeId'
        expect(@player.caption.currentSpeed).toEqual '1.0'
        expect(@player.caption.captionAssetPath).toEqual '/static/subs/'

      it 'create video speed control', ->
        expect(window.VideoSpeedControlAlpha.prototype.initialize).toHaveBeenCalled()
        expect(@player.speedControl).toBeDefined()
        expect(@player.speedControl.el).toBe $('.secondary-controls', @player.el)
        expect(@player.speedControl.speeds).toEqual ['0.75', '1.0']
        expect(@player.speedControl.currentSpeed).toEqual '1.0'

      it 'create video progress slider', ->
        expect(window.VideoSpeedControlAlpha.prototype.initialize).toHaveBeenCalled()
        expect(@player.progressSlider).toBeDefined()
        expect(@player.progressSlider.el).toBe $('.slider', @player.el)

      it 'bind to video control play event', ->
        expect($(@player.control)).toHandleWith 'play', @player.play

      it 'bind to video control pause event', ->
        expect($(@player.control)).toHandleWith 'pause', @player.pause

      it 'bind to video caption seek event', ->
        expect($(@player.caption)).toHandleWith 'caption_seek', @player.onSeek

      it 'bind to video speed control speedChange event', ->
        expect($(@player.speedControl)).toHandleWith 'speedChange', @player.onSpeedChange

      it 'bind to video progress slider seek event', ->
        expect($(@player.progressSlider)).toHandleWith 'slide_seek', @player.onSeek

      it 'bind to video volume control volumeChange event', ->
        expect($(@player.volumeControl)).toHandleWith 'volumeChange', @player.onVolumeChange

      it 'bind to key press', ->
        expect($(document.documentElement)).toHandleWith 'keyup', @player.bindExitFullScreen

      it 'bind to fullscreen switching button', ->
        expect($('.add-fullscreen')).toHandleWith 'click', @player.toggleFullScreen

    it 'create Youtube player', ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      spyOn YT, 'Player'
      @player = new VideoPlayerAlpha video: @video
      expect(YT.Player).toHaveBeenCalledWith('id', {
        playerVars: playerVars
        videoId: 'normalSpeedYoutubeId'
        events:
          onReady: @player.onReady
          onStateChange: @player.onStateChange
          onPlaybackQualityChange: @player.onPlaybackQualityChange
      })

    it 'create HTML5 player', ->
      jasmine.stubVideoPlayerAlpha @, [], false, true
      spyOn HTML5Video, 'Player'
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      expect(HTML5Video.Player).toHaveBeenCalledWith @video.el,
        playerVars: playerVars
        videoSources: @video.html5Sources
        events:
          onReady: @player.onReady
          onStateChange: @player.onStateChange

    describe 'when not on a touch based device', ->
      beforeEach ->
        jasmine.stubVideoPlayerAlpha @, [], false
        $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
        $('.add-fullscreen, .hide-subtitles').removeData 'qtip'
        @player = new VideoPlayerAlpha video: @video

      it 'add the tooltip to fullscreen and subtitle button', ->
        expect($('.add-fullscreen')).toHaveData 'qtip'
        expect($('.hide-subtitles')).toHaveData 'qtip'

      it 'create video volume control', ->
        expect(window.VideoVolumeControlAlpha.prototype.initialize).toHaveBeenCalled()
        expect(@player.volumeControl).toBeDefined()
        expect(@player.volumeControl.el).toBe $('.secondary-controls', @player.el)

    describe 'when on a touch based device', ->
      beforeEach ->
        jasmine.stubVideoPlayerAlpha @, [], false
        $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
        window.onTouchBasedDevice.andReturn true
        $('.add-fullscreen, .hide-subtitles').removeData 'qtip'
        @player = new VideoPlayerAlpha video: @video

      it 'does not add the tooltip to fullscreen and subtitle button', ->
        expect($('.add-fullscreen')).not.toHaveData 'qtip'
        expect($('.hide-subtitles')).not.toHaveData 'qtip'

      it 'does not create video volume control', ->
        expect(window.VideoVolumeControlAlpha.prototype.initialize).not.toHaveBeenCalled()
        expect(@player.volumeControl).not.toBeDefined()

  describe 'onReady', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      spyOn @video, 'log'
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @video.embed()
      @player = @video.player
      spyOnEvent @player, 'ready'
      spyOnEvent @player, 'updatePlayTime'
      @player.onReady()

    it 'log the load_video event', ->
      expect(@video.log).toHaveBeenCalledWith 'load_video'

    describe 'when not on a touch based device', ->
      beforeEach ->
        spyOn @player, 'play'
        @player.onReady()

      it 'autoplay the first video', ->
        expect(@player.play).toHaveBeenCalled()

    describe 'when on a touch based device', ->
      beforeEach ->
        window.onTouchBasedDevice.andReturn true
        spyOn @player, 'play'
        @player.onReady()

      it 'does not autoplay the first video', ->
        expect(@player.play).not.toHaveBeenCalled()

  describe 'onStateChange', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')

    describe 'when the video is unstarted', ->
      beforeEach ->
        @player = new VideoPlayerAlpha video: @video
        spyOn @player.control, 'pause'
        @player.caption.pause = jasmine.createSpy('VideoCaptionAlpha.pause')
        @player.onStateChange data: YT.PlayerState.UNSTARTED

      it 'pause the video control', ->
        expect(@player.control.pause).toHaveBeenCalled()

      it 'pause the video caption', ->
        expect(@player.caption.pause).toHaveBeenCalled()

    describe 'when the video is playing', ->
      beforeEach ->
        @anotherPlayer = jasmine.createSpyObj 'AnotherPlayer', ['onPause']
        window.OldVideoPlayerAlpha = @anotherPlayer
        @player = new VideoPlayerAlpha video: @video
        spyOn @video, 'log'
        spyOn(window, 'setInterval').andReturn 100
        spyOn @player.control, 'play'
        @player.caption.play = jasmine.createSpy('VideoCaptionAlpha.play')
        @player.progressSlider.play = jasmine.createSpy('VideoProgressSliderAlpha.play')
        @player.player.getVideoEmbedCode.andReturn 'embedCode'
        @player.onStateChange data: YT.PlayerState.PLAYING

      it 'log the play_video event', ->
        expect(@video.log).toHaveBeenCalledWith 'play_video', {currentTime: 0}

      it 'pause other video player', ->
        expect(@anotherPlayer.onPause).toHaveBeenCalled()

      it 'set current video player as active player', ->
        expect(window.OldVideoPlayerAlpha).toEqual @player

      it 'set update interval', ->
        expect(window.setInterval).toHaveBeenCalledWith @player.update, 200
        expect(@player.player.interval).toEqual 100

      it 'play the video control', ->
        expect(@player.control.play).toHaveBeenCalled()

      it 'play the video caption', ->
        expect(@player.caption.play).toHaveBeenCalled()

      it 'play the video progress slider', ->
        expect(@player.progressSlider.play).toHaveBeenCalled()

    describe 'when the video is paused', ->
      beforeEach ->
        @player = new VideoPlayerAlpha video: @video
        spyOn @video, 'log'
        spyOn window, 'clearInterval'
        spyOn @player.control, 'pause'
        @player.caption.pause = jasmine.createSpy('VideoCaptionAlpha.pause')
        @player.player.interval = 100
        @player.player.getVideoEmbedCode.andReturn 'embedCode'
        @player.onStateChange data: YT.PlayerState.PAUSED

      it 'log the pause_video event', ->
        expect(@video.log).toHaveBeenCalledWith 'pause_video', {currentTime: 0}

      it 'clear update interval', ->
        expect(window.clearInterval).toHaveBeenCalledWith 100
        expect(@player.player.interval).toBeNull()

      it 'pause the video control', ->
        expect(@player.control.pause).toHaveBeenCalled()

      it 'pause the video caption', ->
        expect(@player.caption.pause).toHaveBeenCalled()

    describe 'when the video is ended', ->
      beforeEach ->
        @player = new VideoPlayerAlpha video: @video
        spyOn @player.control, 'pause'
        @player.caption.pause = jasmine.createSpy('VideoCaptionAlpha.pause')
        @player.onStateChange data: YT.PlayerState.ENDED

      it 'pause the video control', ->
        expect(@player.control.pause).toHaveBeenCalled()

      it 'pause the video caption', ->
        expect(@player.caption.pause).toHaveBeenCalled()

  describe 'onSeek', ->
    conf = [{
        desc : 'check if seek_video is logged with slide_seek type',
        type: 'slide_seek',
        obj: 'progressSlider'
      },{
        desc : 'check if seek_video is logged with caption_seek type',
        type: 'caption_seek',
        obj: 'caption'
      }]

    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      spyOn window, 'clearInterval'
      @player.player.interval = 100
      spyOn @player, 'updatePlayTime'
      spyOn @video, 'log'

    $.each conf, (key, value) ->
      it value.desc, ->
        type = value.type
        old_time = 0
        new_time = 60
        $(@player[value.obj]).trigger value.type, new_time
        expect(@video.log).toHaveBeenCalledWith 'seek_video',
          old_time: old_time
          new_time: new_time
          type: value.type

    it 'seek the player', ->
      $(@player.progressSlider).trigger 'slide_seek', 60
      expect(@player.player.seekTo).toHaveBeenCalledWith 60, true

    it 'call updatePlayTime on player', ->
      $(@player.progressSlider).trigger 'slide_seek', 60
      expect(@player.updatePlayTime).toHaveBeenCalledWith 60

    describe 'when the player is playing', ->
      beforeEach ->
        $(@player.progressSlider).trigger 'slide_seek', 60
        @player.player.getPlayerState.andReturn YT.PlayerState.PLAYING
        @player.onSeek {}, 60

      it 'reset the update interval', ->
        expect(window.clearInterval).toHaveBeenCalledWith 100

    describe 'when the player is not playing', ->
      beforeEach ->
        $(@player.progressSlider).trigger 'slide_seek', 60
        @player.player.getPlayerState.andReturn YT.PlayerState.PAUSED
        @player.onSeek {}, 60

      it 'set the current time', ->
        expect(@player.currentTime).toEqual 60

  describe 'onSpeedChange', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      @player.currentTime = 60
      spyOn @player, 'updatePlayTime'
      spyOn(@video, 'setSpeed').andCallThrough()
      spyOn(@video, 'log')

    describe 'always', ->
      beforeEach ->
        @player.onSpeedChange {}, '0.75', false

      it 'check if speed_change_video is logged', ->
        expect(@video.log).toHaveBeenCalledWith 'speed_change_video',
          currentTime: @player.currentTime
          old_speed: '1.0'
          new_speed: '0.75'

      it 'convert the current time to the new speed', ->
        expect(@player.currentTime).toEqual '80.000'

      it 'set video speed to the new speed', ->
        expect(@video.setSpeed).toHaveBeenCalledWith '0.75', false

      it 'tell video caption that the speed has changed', ->
        expect(@player.caption.currentSpeed).toEqual '0.75'

    describe 'when the video is playing', ->
      beforeEach ->
        @player.player.getPlayerState.andReturn YT.PlayerState.PLAYING
        @player.onSpeedChange {}, '0.75'

      it 'load the video', ->
        expect(@player.player.loadVideoById).toHaveBeenCalledWith 'slowerSpeedYoutubeId', '80.000'

      it 'trigger updatePlayTime event', ->
        expect(@player.updatePlayTime).toHaveBeenCalledWith '80.000'

    describe 'when the video is not playing', ->
      beforeEach ->
        @player.player.getPlayerState.andReturn YT.PlayerState.PAUSED
        @player.onSpeedChange {}, '0.75'

      it 'cue the video', ->
        expect(@player.player.cueVideoById).toHaveBeenCalledWith 'slowerSpeedYoutubeId', '80.000'

      it 'trigger updatePlayTime event', ->
        expect(@player.updatePlayTime).toHaveBeenCalledWith '80.000'

  describe 'onVolumeChange', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      @player.onVolumeChange undefined, 60

    it 'set the volume on player', ->
      expect(@player.player.setVolume).toHaveBeenCalledWith 60

  describe 'update', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      spyOn @player, 'updatePlayTime'

    describe 'when the current time is unavailable from the player', ->
      beforeEach ->
        @player.player.getCurrentTime.andReturn undefined
        @player.update()

      it 'does not trigger updatePlayTime event', ->
        expect(@player.updatePlayTime).not.toHaveBeenCalled()

    describe 'when the current time is available from the player', ->
      beforeEach ->
        @player.player.getCurrentTime.andReturn 60
        @player.update()

      it 'trigger updatePlayTime event', ->
        expect(@player.updatePlayTime).toHaveBeenCalledWith(60)

  describe 'updatePlayTime', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      spyOn(@video, 'getDuration').andReturn 1800
      @player.caption.updatePlayTime = jasmine.createSpy('VideoCaptionAlpha.updatePlayTime')
      @player.progressSlider.updatePlayTime = jasmine.createSpy('VideoProgressSliderAlpha.updatePlayTime')
      @player.updatePlayTime 60

    it 'update the video playback time', ->
      expect($('.vidtime')).toHaveHtml '1:00 / 30:00'

    it 'update the playback time on caption', ->
      expect(@player.caption.updatePlayTime).toHaveBeenCalledWith 60

    it 'update the playback time on progress slider', ->
      expect(@player.progressSlider.updatePlayTime).toHaveBeenCalledWith 60, 1800

  describe 'toggleFullScreen', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      @player.caption.resize = jasmine.createSpy('VideoCaptionAlpha.resize')

    describe 'when the video player is not full screen', ->
      beforeEach ->
        spyOn @video, 'log'
        @player.el.removeClass 'fullscreen'
        @player.toggleFullScreen(jQuery.Event("click"))

      it 'log the fullscreen event', ->
        expect(@video.log).toHaveBeenCalledWith 'fullscreen',
        currentTime: @player.currentTime

      it 'replace the full screen button tooltip', ->
        expect($('.add-fullscreen')).toHaveAttr 'title', 'Exit fill browser'

      it 'add the fullscreen class', ->
        expect(@player.el).toHaveClass 'fullscreen'

      it 'tell VideoCaption to resize', ->
        expect(@player.caption.resize).toHaveBeenCalled()

    describe 'when the video player already full screen', ->
      beforeEach ->
        spyOn @video, 'log'
        @player.el.addClass 'fullscreen'
        @player.toggleFullScreen(jQuery.Event("click"))

      it 'log the not_fullscreen event', ->
        expect(@video.log).toHaveBeenCalledWith 'not_fullscreen',
        currentTime: @player.currentTime

      it 'replace the full screen button tooltip', ->
        expect($('.add-fullscreen')).toHaveAttr 'title', 'Fill browser'

      it 'remove exit full screen button', ->
        expect(@player.el).not.toContain 'a.exit'

      it 'remove the fullscreen class', ->
        expect(@player.el).not.toHaveClass 'fullscreen'

      it 'tell VideoCaption to resize', ->
        expect(@player.caption.resize).toHaveBeenCalled()

  describe 'play', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video

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
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video

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
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      @player.pause()

    it 'delegate to the Youtube player', ->
      expect(@player.player.pauseVideo).toHaveBeenCalled()

  describe 'duration', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      spyOn @video, 'getDuration'
      @player.duration()

    it 'delegate to the video', ->
      expect(@video.getDuration).toHaveBeenCalled()

  describe 'currentSpeed', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      @video.speed = '3.0'

    it 'delegate to the video', ->
      expect(@player.currentSpeed()).toEqual '3.0'

  describe 'volume', ->
    beforeEach ->
      jasmine.stubVideoPlayerAlpha @, [], false
      $('.video').append $('<div class="add-fullscreen" /><div class="hide-subtitles" />')
      @player = new VideoPlayerAlpha video: @video
      @player.player.getVolume.andReturn 42

    describe 'without value', ->
      it 'return current volume', ->
        expect(@player.volume()).toEqual 42

    describe 'with value', ->
      it 'set player volume', ->
        @player.volume(60)
        expect(@player.player.setVolume).toHaveBeenCalledWith(60)
