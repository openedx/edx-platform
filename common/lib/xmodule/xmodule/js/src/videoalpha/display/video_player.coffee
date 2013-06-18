class @VideoPlayerAlpha extends SubviewAlpha
  initialize: ->
    # If we switch verticals while the video is playing, then HTML content is
    # removed, but JS code is still executing (setInterval() method), and there will
    # arise conflicts (no HTML content, but code tries to access it). Therefore
    # we must pause the player (stop setInterval() method).
    if (window.OldVideoPlayerAlpha) and (window.OldVideoPlayerAlpha.onPause)
      window.OldVideoPlayerAlpha.onPause()
    window.OldVideoPlayerAlpha = @

    if @video.videoType is 'youtube'
      @PlayerState = YT.PlayerState
      # Define a missing constant of Youtube API
      @PlayerState.UNSTARTED = -1
    else if @video.videoType is 'html5'
      @PlayerState = HTML5Video.PlayerState

    @currentTime = 0
    @el = $("#video_#{@video.id}")

  bind: ->
    $(@control).bind('play', @play)
      .bind('pause', @pause)
    if @video.videoType is 'youtube'
      $(@qualityControl).bind('changeQuality', @handlePlaybackQualityChange)
    if @video.show_captions is true
      $(@caption).bind('caption_seek', @onSeek)
    $(@speedControl).bind('speedChange', @onSpeedChange)
    $(@progressSlider).bind('slide_seek', @onSeek)
    if @volumeControl
      $(@volumeControl).bind('volumeChange', @onVolumeChange)
    $(document.documentElement).keyup @bindExitFullScreen

    @$('.add-fullscreen').click @toggleFullScreen
    @addToolTip() unless onTouchBasedDevice()

  bindExitFullScreen: (event) =>
    if @el.hasClass('fullscreen') && event.keyCode == 27
      @toggleFullScreen(event)

  render: ->
    @control = new VideoControlAlpha el: @$('.video-controls')
    if @video.videoType is 'youtube'
      @qualityControl = new VideoQualityControlAlpha el: @$('.secondary-controls')
    if @video.show_captions is true
      @caption = new VideoCaptionAlpha
        el: @el
        video: @video
        player: @
        youtubeId: @video.youtubeId('1.0')
        currentSpeed: @currentSpeed()
        captionAssetPath: @video.caption_asset_path
    unless onTouchBasedDevice()
      @volumeControl = new VideoVolumeControlAlpha el: @$('.secondary-controls')
    @speedControl = new VideoSpeedControlAlpha el: @$('.secondary-controls'), speeds: @video.speeds, currentSpeed: @currentSpeed()
    @progressSlider = new VideoProgressSliderAlpha el: @$('.slider')
    @playerVars =
      controls: 0
      wmode: 'transparent'
      rel: 0
      showinfo: 0
      enablejsapi: 1
      modestbranding: 1
      html5: 1
    if @video.start
      @playerVars.start = @video.start
      @playerVars.wmode = 'window'
    if @video.end
      # work in AS3, not HMLT5. but iframe use AS3
      @playerVars.end = @video.end

    # There is a bug which prevents YouTube API to correctly set the speed to 1.0 from another speed
    # in Firefox when in HTML5 mode. There is a fix which basically reloads the video at speed 1.0
    # when this change is requested (instead of simply requesting a speed change to 1.0). This has to
    # be done only when the video is being watched in Firefox. We need to figure out what browser is
    # currently executing this code.
    #
    # TODO: Check the status of http://code.google.com/p/gdata-issues/issues/detail?id=4654
    #       When the YouTube team fixes the API bug, we can remove this temporary bug fix.
    @video.isFirefox = navigator.userAgent.toLowerCase().indexOf('firefox') > -1

    if @video.videoType is 'html5'
      @video.playerType = 'browser'
      @player = new HTML5Video.Player @video.el,
        playerVars: @playerVars,
        videoSources: @video.html5Sources,
        events:
          onReady: @onReady
          onStateChange: @onStateChange
    else if @video.videoType is 'youtube'
      prev_player_type = $.cookie('prev_player_type')
      if prev_player_type == 'html5'
        youTubeId = @video.videos['1.0']
      else
        youTubeId = @video.youtubeId()
      @video.playerType = 'youtube'
      @player = new YT.Player @video.id,
        playerVars: @playerVars
        videoId: youTubeId
        events:
          onReady: @onReady
          onStateChange: @onStateChange
          onPlaybackQualityChange: @onPlaybackQualityChange
    if @video.show_captions is true
      @caption.hideCaptions(@['video'].hide_captions)

  addToolTip: ->
    @$('.add-fullscreen, .hide-subtitles').qtip
      position:
        my: 'top right'
        at: 'top center'

  onReady: (event) =>
    @video.log 'load_video'
    if @video.videoType is 'html5'
      @player.setPlaybackRate @video.speed
    if not onTouchBasedDevice() and $('.video:first').data('autoplay') isnt 'False'
      $('.video-load-complete:first').data('video').player.play()

  onStateChange: (event) =>
    _this = this
    switch event.data
      when @PlayerState.UNSTARTED
        # Before the video starts playing, let us see if we are in YouTube player,
        # and if YouTube is in HTML5 mode. If both cases are true, then we can make
        # it so that speed switching happens natively.

        if @video.videoType is "youtube"
          # Because YouTube API does not have a direct method to determine the mode we
          # are in (Flash or HTML5), we rely on an indirect method. Currently, when in
          # Flash mode, YouTube player reports that there is only one (1.0) speed
          # available. When in HTML5 mode, it reports multiple speeds available. We
          # will use this fact.
          #
          # NOTE: It is my strong belief that in the future YouTube Flash player will
          # not get speed changes. This is a dying technology. So we can safely use
          # this indirect method to determine player mode.
          availableSpeeds = @player.getAvailablePlaybackRates()
          prev_player_type = $.cookie('prev_player_type')
          if availableSpeeds.length > 1
            # If the user last accessed the page and watched a movie via YouTube
            # player, and it was using Flash mode, then we must reset the current
            # YouTube speed to 1.0 (by loading appropriate video that is encoded at
            # 1.0 speed).
            if prev_player_type == 'youtube'
              $.cookie('prev_player_type', 'html5', expires: 3650, path: '/')
              @onSpeedChange null, '1.0', false
            else if prev_player_type != 'html5'
              $.cookie('prev_player_type', 'html5', expires: 3650, path: '/')

            # Now we must update all the speeds to the ones available via the YouTube
            # HTML5 API. The default speeds are not exactly the same as reported by
            # YouTube, so we will remove the default speeds, and populate all the
            # necessary data with correct available speeds.
            baseSpeedSubs = @video.videos["1.0"]
            $.each @video.videos, (index, value) ->
              delete _this.video.videos[index]
            @video.speeds = []
            $.each availableSpeeds, (index, value) ->
              _this.video.videos[value.toFixed(2).replace(/\.00$/, ".0")] = baseSpeedSubs
              _this.video.speeds.push value.toFixed(2).replace(/\.00$/, ".0")

            # We must update the Speed Control to reflect the new avialble speeds.
            @speedControl.reRender @video.speeds, @video.speed

            # Now we set the videoType to 'HTML5'. This works because my HTML5Video
            # class is fully compatible with YouTube HTML5 API.
            @video.videoType = 'html5'

            @video.setSpeed $.cookie('video_speed')

            # Change the speed to the required one.
            @player.setPlaybackRate @video.speed
          else
            # We are in YouTube player, and in Flash mode. Check previos mode.
            if prev_player_type != 'youtube'
              $.cookie('prev_player_type', 'youtube', expires: 3650, path: '/')

              # We need to set the proper speed when previous mode was not 'youtube'.
              @onSpeedChange null, $.cookie('video_speed')

        @onUnstarted()
      when @PlayerState.PLAYING
        @onPlay()
      when @PlayerState.PAUSED
        @onPause()
      when @PlayerState.ENDED
        @onEnded()

  onPlaybackQualityChange: (event, value) =>
    quality = @player.getPlaybackQuality()
    @qualityControl.onQualityChange(quality)

  handlePlaybackQualityChange: (event, value) =>
    @player.setPlaybackQuality(value)

  onUnstarted: =>
    @control.pause()
    if @video.show_captions is true
      @caption.pause()

  onPlay: =>
    @video.log 'play_video',
      currentTime: @currentTime
    unless @player.interval
      @player.interval = setInterval(@update, 200)
    if @video.show_captions is true
      @caption.play()
    @control.play()
    @progressSlider.play()

  onPause: =>
    @video.log 'pause_video',
      currentTime: @currentTime
    clearInterval(@player.interval)
    @player.interval = null
    if @video.show_captions is true
      @caption.pause()
    @control.pause()

  onEnded: =>
    @control.pause()
    if @video.show_captions is true
      @caption.pause()

  onSeek: (event, time) =>
    @video.log 'seek_video',
      old_time: @currentTime
      new_time: time
      type: event.type
    @player.seekTo(time, true)
    if @isPlaying()
      clearInterval(@player.interval)
      @player.interval = setInterval(@update, 200)
    else
      @currentTime = time
    @updatePlayTime time

  onSpeedChange: (event, newSpeed, updateCookie) =>
    if @video.videoType is 'youtube'
      @currentTime = Time.convert(@currentTime, parseFloat(@currentSpeed()), newSpeed)
    newSpeed = parseFloat(newSpeed).toFixed(2).replace /\.00$/, '.0'

    @video.log 'speed_change_video',
      currentTime: @currentTime
      old_speed: @currentSpeed()
      new_speed: newSpeed

    @video.setSpeed newSpeed, updateCookie
    if @video.videoType is 'youtube'
      if @video.show_captions is true
        @caption.currentSpeed = newSpeed

    # We request the reloading of the video in the case when YouTube is in Flash player mode,
    # or when we are in Firefox, and the new speed is 1.0. The second case is necessary to
    # avoid the bug where in Firefox speed switching to 1.0 in HTML5 player mode is handled
    # incorrectly by YouTube API.
    #
    # TODO: Check the status of http://code.google.com/p/gdata-issues/issues/detail?id=4654
    #       When the YouTube team fixes the API bug, we can remove this temporary bug fix.
    if (@video.videoType is 'youtube') or ((@video.isFirefox) and (@video.playerType is 'youtube') and (newSpeed is '1.0'))
      if @isPlaying()
        @player.loadVideoById(@video.youtubeId(), @currentTime)
      else
        @player.cueVideoById(@video.youtubeId(), @currentTime)
    else if @video.videoType is 'html5'
      @player.setPlaybackRate newSpeed
    if @video.videoType is 'youtube'
      @updatePlayTime @currentTime

  onVolumeChange: (event, volume) =>
    @player.setVolume volume

  update: =>
    if @currentTime = @player.getCurrentTime()
      @updatePlayTime @currentTime

  updatePlayTime: (time) ->
    progress = Time.format(time) + ' / ' + Time.format(@duration())
    @$(".vidtime").html(progress)
    if @video.show_captions is true
      @caption.updatePlayTime(time)
    @progressSlider.updatePlayTime(time, @duration())

  toggleFullScreen: (event) =>
    event.preventDefault()
    if @el.hasClass('fullscreen')
      type = 'not_fullscreen'
      @$('.add-fullscreen').attr('title', 'Fill browser')
      @el.removeClass('fullscreen')
    else
      type = 'fullscreen'
      @el.addClass('fullscreen')
      @$('.add-fullscreen').attr('title', 'Exit fill browser')
    @video.log type,
      currentTime: @currentTime
    if @video.show_captions is true
      @caption.resize()

  # Delegates
  play: =>
    @player.playVideo() if @player.playVideo

  isPlaying: ->
    @player.getPlayerState() == @PlayerState.PLAYING

  pause: =>
    @player.pauseVideo() if @player.pauseVideo

  duration: ->
    duration = @player.getDuration() if @player.getDuration
    if isFinite(duration) is false
      duration = @video.getDuration()
    duration

  currentSpeed: ->
    @video.speed

  volume: (value) ->
    if value?
      @player.setVolume value
    else
      @player.getVolume()
