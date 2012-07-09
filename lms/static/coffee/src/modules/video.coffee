class @Video
  constructor: (@id, videos) ->
    window.player = null
    @el = $("#video_#{@id}")
    @parseVideos videos
    @fetchMetadata()
    @parseSpeed()
    $("#video_#{@id}").data('video', this)

    if YT.Player
      @embed()
    else
      window.onYouTubePlayerAPIReady = =>
        $('.course-content .video').each ->
          $(this).data('video').embed()

  youtubeId: (speed)->
    @videos[speed || @speed]

  parseVideos: (videos) ->
    @videos = {}
    $.each videos.split(/,/), (index, video) =>
      video = video.split(/:/)
      speed = parseFloat(video[0]).toFixed(2).replace /\.00$/, '.0'
      @videos[speed] = video[1]

  parseSpeed: ->
    @setSpeed($.cookie('video_speed'))
    @speeds = ($.map @videos, (url, speed) -> speed).sort()

  setSpeed: (newSpeed) ->
    if @videos[newSpeed] != undefined
      @speed = newSpeed
      $.cookie('video_speed', "#{newSpeed}", expires: 3650, path: '/')
    else
      @speed = '1.0'

  embed: ->
    @player = new VideoPlayer video: this

  fetchMetadata: (url) ->
    @metadata = {}
    $.each @videos, (speed, url) =>
      $.get "http://gdata.youtube.com/feeds/api/videos/#{url}?v=2&alt=jsonc", ((data) => @metadata[data.data.id] = data.data) , 'jsonp'

  getDuration: ->
    @metadata[@youtubeId()].duration

  log: (eventName) ->
    Logger.log eventName,
      id: @id
      code: @youtubeId()
      currentTime: @player.currentTime
      speed: @speed
