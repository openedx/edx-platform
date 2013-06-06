class @Video
  constructor: (element) ->
    @el = $(element).find('.video')
    @id = @el.attr('id').replace(/video_/, '')
    @start = @el.data('start')
    @end = @el.data('end')
    @caption_asset_path = @el.data('caption-asset-path')
    @show_captions = @el.data('show-captions') == "true"
    window.player = null
    @el = $("#video_#{@id}")
    @parseVideos()
    @fetchMetadata()
    @parseSpeed()
    $("#video_#{@id}").data('video', this).addClass('video-load-complete')

    @hide_captions = $.cookie('hide_captions') == 'true'

    if YT.Player
      @embed()
    else
      window.onYouTubePlayerAPIReady = =>
        @el.each ->
          $(this).data('video').embed()

  youtubeId: (speed)->
    @videos[speed || @speed]

  parseVideos: (videos) ->
    @videos = {}
    @videos['.75'] = @el.data('youtube-id-0-75')
    @videos['1.0'] = @el.data('normal-speed-video-id')
    @videos['1.25'] = @el.data('youtube-id-1-25')
    @videos['1.5'] = @el.data('youtube-id-1-5')
    alert @videos['1.5']

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
      $.get "https://gdata.youtube.com/feeds/api/videos/#{url}?v=2&alt=jsonc", ((data) => @metadata[data.data.id] = data.data) , 'jsonp'

  getDuration: ->
    @metadata[@youtubeId()].duration

  log: (eventName) ->
    Logger.log eventName,
      id: @id
      code: @youtubeId()
      currentTime: @player.currentTime
      speed: @speed
