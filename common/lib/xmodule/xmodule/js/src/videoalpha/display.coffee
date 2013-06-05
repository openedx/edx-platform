class @VideoAlpha
  constructor: (element) ->
    @el = $(element).find('.video')
    @id = @el.attr('id').replace(/video_/, '')
    @start = @el.data('start')
    @end = @el.data('end')
    @caption_data_dir = @el.data('caption-data-dir')
    @caption_asset_path = @el.data('caption-asset-path')
    @show_captions = @el.data('show-captions').toString() == "true"
    @el = $("#video_#{@id}")
    if @parseYoutubeId(@el.data("streams")) is true
      @videoType = "youtube"
      @fetchMetadata()
      @parseSpeed()
    else
      @videoType = "html5"
      @parseHtml5Sources @el.data('mp4-source'), @el.data('webm-source'), @el.data('ogg-source')
      @speeds = ['0.75', '1.0', '1.25', '1.50']
      sub = @el.data('sub')
      if (typeof sub isnt "string") or (sub.length is 0)
        sub = ""
        @show_captions = false
      @videos =
        "0.75": sub
        "1.0": sub
        "1.25": sub
        "1.5": sub
      @setSpeed $.cookie('video_speed')
    $("#video_#{@id}").data('video', this).addClass('video-load-complete')
    if @show_captions is true
      @hide_captions = $.cookie('hide_captions') == 'true'
    else
      @hide_captions = true
      $.cookie('hide_captions', @hide_captions, expires: 3650, path: '/')
      @el.addClass 'closed'
    if ((@videoType is "youtube") and (YT.Player)) or ((@videoType is "html5") and (HTML5Video.Player))
      @embed()
    else
      if @videoType is "youtube"
        window.onYouTubePlayerAPIReady = =>
          @embed()
      else if @videoType is "html5"
        window.onHTML5PlayerAPIReady = =>
          @embed()

  youtubeId: (speed)->
    @videos[speed || @speed]

  parseYoutubeId: (videos)->
    return false  if (typeof videos isnt "string") or (videos.length is 0)
    @videos = {}
    $.each videos.split(/,/), (index, video) =>
      speed = undefined
      video = video.split(/:/)
      speed = parseFloat(video[0]).toFixed(2).replace(/\.00$/, ".0")
      @videos[speed] = video[1]
    true

  parseHtml5Sources: (mp4Source, webmSource, oggSource)->
    @html5Sources =
      mp4: null
      webm: null
      ogg: null
    @html5Sources.mp4 = mp4Source  if (typeof mp4Source is "string") and (mp4Source.length > 0)
    @html5Sources.webm = webmSource  if (typeof webmSource is "string") and (webmSource.length > 0)
    @html5Sources.ogg = oggSource  if (typeof oggSource is "string") and (oggSource.length > 0)

  parseSpeed: ->
    @speeds = ($.map @videos, (url, speed) -> speed).sort()
    @setSpeed $.cookie('video_speed')

  setSpeed: (newSpeed, updateCookie)->
    if @speeds.indexOf(newSpeed) isnt -1
      @speed = newSpeed

      if updateCookie isnt false
        $.cookie "video_speed", "" + newSpeed,
          expires: 3650
          path: "/"
    else
      @speed = "1.0"

  embed: ->
    @player = new VideoPlayerAlpha video: this

  fetchMetadata: (url) ->
    @metadata = {}
    $.each @videos, (speed, url) =>
      $.get "https://gdata.youtube.com/feeds/api/videos/#{url}?v=2&alt=jsonc", ((data) => @metadata[data.data.id] = data.data) , 'jsonp'

  getDuration: ->
    @metadata[@youtubeId()].duration

  log: (eventName, data)->
    # Default parameters that always get logged.
    logInfo =
      id: @id
      code: @youtubeId()

    # If extra parameters were passed to the log.
    if data
      $.each data, (paramName, value) ->
        logInfo[paramName] = value

    if @videoType is "youtube"
      logInfo.code = @youtubeId()
    else logInfo.code = "html5"  if @videoType is "html5"
    Logger.log eventName, logInfo
