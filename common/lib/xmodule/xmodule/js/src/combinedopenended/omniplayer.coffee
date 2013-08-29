class @OmniPlayer
  type: undefined
  videoId: undefined
  height: undefined
  width: undefined
  elementId: undefined
  startSeconds: undefined
  endSeconds: undefined
  internal: undefined
  @loaded:
    YT: false
    TEST: false
    JW: false

  constructor: (obj) ->
    @elementId = obj.elementId
    @videoId = obj.videoId
    @videoType = obj.videoType or obj.type
    @height = obj.height
    @width = obj.width
    @startSeconds = obj.startSeconds
    @endSeconds = obj.endSeconds

    @mediaContentUrl = obj.mediaContentUrl
    @thumbnailUrl = obj.thumbnailUrl

    # set default height and width
    @height = $("##{@elementId}").height() if !@height?
    @width = $("##{@elementId}").width() if !@width?

    OmniPlayer[@videoType].createPlayer.apply(this, [obj])

  getDuration: ->
    throw new Error "getDuration isn't defined for OmniPlayer type #{@videoType}"

  getCurrentTime: ->
    throw new Error "getCurrentTime isn't not defined for OmniPlayer type #{@videoType}"   

  stopVideo: ->
    throw new Error "stopVideo isn't not defined for OmniPlayer type #{@videoType}"

  cueVideoById: (options) ->
    throw new Error "cueVideoById isn't not defined for OmniPlayer type #{@videoType}"

  cueVideoByUrl: (options) ->
    throw new Error "cueVideoByUrl isn't not defined for OmniPlayer type #{@videoType}"

  loadVideoById: (options) -> 
    throw new Error "loadVideoById isn't not defined for OmniPlayer type #{@videoType}"

  loadVideoById: (options) -> 
    throw new Error "loadVideoByUrl isn't not defined for OmniPlayer type #{@videoType}"

  remove: ->
    el = $("##{@elementId}")
    new_el = el.after("<div></div>").next()

    el.remove()
    new_el.attr
      id: "#{@elementId}"
    return this

  @JW:
    setup: (started) ->
      if !@mediaContentUrl? && @videoId?
        @mediaContentUrl = "http://www.youtube.com/watch?v=#{@videoId}"

      if !@thumbnailUrl? && @videoId?
        @thumbnailUrl = "http://img.youtube.com/vi/#{@videoId}/0.jpg"

      @internal = jwplayer(@elementId).setup
        file: @mediaContentUrl
        image: @thumbnailUrl
        height: @height
        width: @width

      that = this
      @internal.seek(@startSeconds)

      @internal.onPlay () ->
        if !started
          started = true
          that.internal.pause()

      @internal.onTime (e) ->
        if e.position > that.endSeconds
          that.stopVideo()

      @internal.onIdle (e) ->
        started = false
        that.internal.seek(that.startSeconds)

    build: (obj) ->

      OmniPlayer.JW.setup.apply this, [false]

      @getDuration = ->
        @internal.getDuration()

      @getCurrentTime = ->
        @internal.getPosition()

      @stopVideo = ->
        @internal.stop()

      @cueVideoByUrl = (options) ->
        @internal.remove() if @internal?

        @endSeconds = options.endSeconds
        @startSeconds = options.startSeconds
        @mediaContentUrl = options.mediaContentUrl
        @thumbnailUrl = options.thumbnailUrl

        OmniPlayer.JW.setup.apply this, [false]

      @cueVideoById = (options) ->
        @internal.remove() if @internal?

        @endSeconds = options.endSeconds
        @startSeconds = options.startSeconds
        @videoId = options.videoId

        OmniPlayer.JW.setup.apply this, [false]


      @loadVideoById = (options) ->
        @internal.remove() if @internal?

        @endSeconds = options.endSeconds
        @startSeconds = options.startSeconds
        @videoId = options.videoId

        OmniPlayer.JW.setup.apply this, [true]

      @loadVideoByUrl = (options) ->
        @internal.remove() if @internal?

        @endSeconds = options.endSeconds
        @startSeconds = options.startSeconds
        @mediaContentUrl = options.mediaContentUrl
        @thumbnailUrl = options.thumbnailUrl

        OmniPlayer.JW.setup.apply this, [true]

      @remove = ->
        @internal.remove()

    createPlayer: (obj) ->
      if jwplayer.key?
        OmniPlayer.JW.build.apply this, [obj]
        OmniPlayer.loaded.JW = true
      else
        throw new Error 'jwplayer.key is not defined'

  @YT: 
    setup: ->
      tag = document.createElement("script")
      tag.src = "https://www.youtube.com/iframe_api"
      firstScriptTag = document.getElementsByTagName("script")[0]
      firstScriptTag.parentNode.insertBefore tag, firstScriptTag

    build: ->
      @internal = new window.YT.Player(@elementId,
        videoId: @videoId
        height: @height
        width: @width
        events: {
          onReady: (event) =>
            if @startSeconds || @endSeconds
              event.target.cueVideoById
                videoId: @videoId
                startSeconds: @startSeconds
                endSeconds: @endSeconds
                suggestedQuality: "large"
            else
              @startSeconds = 0 
              @endSeconds = @endSeconds or @getDuration()
        }
      )

      # Encapsulate YouTube API functions
      @getDuration = ->
        @internal.getDuration()

      @getCurrentTime = ->
        @internal.getCurrentTime()

      @stopVideo = ->
        @internal.stopVideo()

      @cueVideoByUrl = (options) ->
        options.suggestedQuality = "large" if !options.suggestedQuality?
        @internal.cueVideoByUrl = (options)

      @cueVideoById = (options) ->
        options.suggestedQuality = "large" if !options.suggestedQuality?
        @internal.cueVideoById(options)

      @loadVideoById = (options) ->
        options.suggestedQuality = "large" if !options.suggestedQuality?
        @internal.loadVideoById(options)

      @loadVideoByUrl = (options) ->
        options.suggestedQuality = "large" if !options.suggestedQuality?
        @internal.loadVideoByUrl = (options)

    createPlayer: (obj)->

      that = this

      if OmniPlayer.loaded.YT
        OmniPlayer.YT.build.apply this
      else
        window.onYouTubeIframeAPIReady = () ->
          OmniPlayer.loaded.YT = true
          OmniPlayer.YT.build.apply that

        OmniPlayer.YT.setup()

  @TEST:
    createPlayer: (obj)->
      OmniPlayer.loaded.TEST = true

      @getDuration = ->
        return 0

      @getCurrentTime = ->
        return 0    

      @stopVideo = ->
        return 0

      @cueVideoById = (options) ->
        return 0

      @cueVideoByUrl = (options) ->
        return 0

      @loadVideoById = (options) -> 
        return 0

      @loadVideoByUrl = (options) -> 
        return 0

if window.onOmniPlayerReady?
  OmniPlayer.ranCallback = true
  window.onOmniPlayerReady()
