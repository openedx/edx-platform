class @VideoPlayer extends Subview
  initialize: ->
    # Define a missing constant of Youtube API
    YT.PlayerState.UNSTARTED = -1

    @currentTime = 0
    @el = $("#video_#{@video.id}")

  bind: ->
    $(@control).bind('play', @play)
      .bind('pause', @pause)
    $(@caption).bind('seek', @onSeek)
    $(@speedControl).bind('speedChange', @onSpeedChange)
    $(@progressSlider).bind('seek', @onSeek)
    if @volumeControl
      $(@volumeControl).bind('volumeChange', @onVolumeChange)
    $(document).keyup @bindExitFullScreen

    @$('.add-fullscreen').click @toggleFullScreen
    @addToolTip() unless onTouchBasedDevice()

  bindExitFullScreen: (event) =>
    if @el.hasClass('fullscreen') && event.keyCode == 27
      @toggleFullScreen(event)

  render: ->
    params = { allowScriptAccess: "always" };
    atts = { id: @videoid };
    youtubeId = @video.youtubeId()

    swfobject.embedSWF("http://www.youtube.com/v/#{youtubeId}?enablejsapi=1&version=3&playerapiid=ytplayer",
                         @video.id, "425", "356", "9", null, null, params, atts )


  addToolTip: ->
    @$('.add-fullscreen, .hide-subtitles').qtip
      position:
        my: 'top right'
        at: 'top center'

  onReady: =>
    unless onTouchBasedDevice()
      $('.video-load-complete:first').data('video').player.play()

  onStateChange: (event) =>
    switch event.data
      when YT.PlayerState.UNSTARTED
        @onUnstarted()
      when YT.PlayerState.PLAYING
        @onPlay()
      when YT.PlayerState.PAUSED
        @onPause()
      when YT.PlayerState.ENDED
        @onEnded()

  onUnstarted: =>
    @control.pause()
    @caption.pause()

  onPlay: =>
    @video.log 'play_video'
    window.player.pauseVideo() if window.player && window.player != @player
    window.player = @player
    unless @player.interval
      @player.interval = setInterval(@update, 200)
    @caption.play()
    @control.play()
    @progressSlider.play()

  onPause: =>
    @video.log 'pause_video'
    window.player = null if window.player == @player
    clearInterval(@player.interval)
    @player.interval = null
    @caption.pause()
    @control.pause()

  onEnded: =>
    @control.pause()
    @caption.pause()

  onSeek: (event, time) =>
    @player.seekTo(time, true)
    if @isPlaying()
      clearInterval(@player.interval)
      @player.interval = setInterval(@update, 200)
    else
      @currentTime = time
    @updatePlayTime time

  onSpeedChange: (event, newSpeed) =>
    @currentTime = Time.convert(@currentTime, parseFloat(@currentSpeed()), newSpeed)
    newSpeed = parseFloat(newSpeed).toFixed(2).replace /\.00$/, '.0'
    @video.setSpeed(newSpeed)
    @caption.currentSpeed = newSpeed

    if @isPlaying()
      @player.loadVideoById(@video.youtubeId(), @currentTime)
    else
      @player.cueVideoById(@video.youtubeId(), @currentTime)
    @updatePlayTime @currentTime

  onVolumeChange: (event, volume) =>
    @player.setVolume volume

  update: =>
    if @currentTime = @player.getCurrentTime()
      @updatePlayTime @currentTime

  updatePlayTime: (time) ->
    progress = Time.format(time) + ' / ' + Time.format(@duration())
    @$(".vidtime").html(progress)
    @caption.updatePlayTime(time)
    @progressSlider.updatePlayTime(time, @duration())

  toggleFullScreen: (event) =>
    event.preventDefault()
    if @el.hasClass('fullscreen')
      @$('.add-fullscreen').attr('title', 'Fill browser')
      @el.removeClass('fullscreen')
    else
      @el.addClass('fullscreen')
      @$('.add-fullscreen').attr('title', 'Exit fill browser')
    @caption.resize()

  # Delegates
  play: =>
    @player.playVideo() if @player.playVideo

  isPlaying: ->
    @player.getPlayerState() == YT.PlayerState.PLAYING

  pause: =>
    @player.pauseVideo() if @player.pauseVideo

  duration: ->
    @video.getDuration()

  currentSpeed: ->
    @video.speed

  volume: (value) ->
    if value?
      @player.setVolume value
    else
      @player.getVolume()
