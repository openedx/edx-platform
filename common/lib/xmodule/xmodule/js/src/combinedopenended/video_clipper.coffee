###
  VideoClipper
  By: Cody Coleman (colemanc@mit.edu)
  Description: VideoClipper is a tool to enhance open ended responses. It
  allows students to embed video clips directly into text. This file contains
  two classes: VideoClipper and OmniPlayer. VideoClipper generates html and
  handles user interactions, while OmniPlayer abstracts away video player 
  specifics for VideoClipper. Currently, Omniplayer only works with YouTube, 
  but additional players, including the edx player, can be added with small 
  additions to OmniPlayer requiring no further changes to the VideoClipper 
  class 
###
class @VideoClipper

  # Instance Variables
  startTime: ""
  endTime: ""
  caretPos: 0
  answerClass: ""
  videoId: "" # video id
  videoType: "" # YT, TEST
  generate: true
  buttonId: ""
  textareaId: ""
  clips: []
  questionBox = null # the question box as a jQuery object
  snippetButton = null # the button to open snippet box as a jQuery object

  # Class Variables 
  @reel: 'http://web.mit.edu/colemanc/www/bookmarklet/images/film3Small.png'
  @player: false
  @playerV: false
  @answerClass: "bookMarklet-answer"
  @generateHtml: true
  @clipper: ""
  @clippers: []
  @callback = false
  @prepared:
    snippet: false

  constructor: (obj)->
    obj = obj or {}

    # Required textarea id used for storing the answer
    @textareaId = obj.textareaId 

    # Required video id for embeds
    @videoId = obj.videoId 

    # Required video type as specified by Omniplayer
    @videoType = obj.videoType 

    # Optional URL for video file if the player type plays files directly
    @mediaContentUrl = obj.mediaContentUrl

    # Optional URL for thumbnail to be display by the player
    @thumbnailUrl = obj.thumbnailUrl 

    # Optional URL for embed thumbnail
    @reel = obj.reel or VideoClipper.reel

    # Optional class name to be added to the div that replaces the textarea
    @answerClass = obj.answerClass or VideoClipper.answerClass

    # Optional id for a button to be used as the snipper button
    @buttonId = obj.buttonId or "bl-"+@videoType + @videoId

    # Optional boolean to specify whether or not VideoClipper should generate 
    # the necessary HTML. Mainly used for testing.
    @generate = if obj.generate != undefined then obj.generate else VideoClipper.generateHtml

    # This condition is mainly used for testing
    @setup() if @generate

    # Adds the new instance to the classes list of all instances
    VideoClipper.clippers = VideoClipper.clippers.concat(this)

  ###
  Description: Removes the html generate by a instance of VideoClipper
  params: N/A
  returns: a VideoClipper instance
  ###
  destroy: ->
    @questionBox.remove() if @questionBox?
    @snippetButton.remove() if @snippetButton?
    return this

  ###
  Description: Generates a contenteditable div to display the video clips
  params: N/A
  returns: a VideoClipper instance
  ###
  generateQuestionBox: () =>
    element = $("#"+@textareaId)
    w = element.width()
    h = element.height()
    content = element.val()

    # Newly created div for answer input
    @questionBox = element.after("<div></div>").css("display", "none").next()

    @questionBox.attr(contenteditable: "true").addClass(@answerClass).css
      width: w
      height: h

    dataString = VideoClipper.generateBLDataString "generate", this

    blDataEncoded = encodeURI(dataString)

    if $('#'+@buttonId).length > 0
      $('#'+@buttonId).attr
        "data-bl": blDataEncoded
        rel: "blModal"
    else
      @questionBox.after("<input type='button' value='Snippet'>").next().attr
        "data-bl": blDataEncoded
        rel: "blModal"
        id: @buttonId

    that = this

    @snippetButton = $('#'+@buttonId)

    @snippetButton.click ->
      VideoClipper.modal.open this, that
      return

    return this

  ###
  Description: Gets the current caret position in the editableDiv, including 
    the generated text inside the video clips
  params: editableDiv - jQuery element to get the caret position from
  returns: the current caret position as a number
  ###
  getCaretPosition: (editableDiv) =>
    @caretPos = 0
    containerEl = null
    sel = undefined
    range = undefined
    if window.getSelection()?
      sel = window.getSelection()
      if sel.rangeCount
        range = sel.getRangeAt(0)
        if range.commonAncestorContainer.parentNode is editableDiv
          temp1 = range.endContainer.data
          temp2 = range.commonAncestorContainer.parentNode.innerHTML.replace(/&nbsp;/g, String.fromCharCode(160))
          temp2 = VideoClipper.stripHTML(temp2)
          @caretPos = range.endOffset + temp2.split(temp1)[0].length
    @caretPos

  ###
  Description: Sets up all the html and event listeners to make 
    the VideoClipper work
  params: N/A
  returns: a instance of VideoClipper
  ###
  setup: =>
    @generateQuestionBox()
    VideoClipper.generate(this)
    return this

  ###
  Description: Adds the newTag to the questionBox at the current caret position
  params: newTag - new video clip as generated by VideoClipper.generateTag
  returns: a instance of VideoClipper
  ###
  update: (newTag) =>
    currContent = @questionBox.contents()
    newContent = []
    beginPos = 0
    endPos = 0
    if currContent.length is 0
      newContent = newTag
    else
      currContent.each (i, e) =>
        if ((e.nodeType is 3) or (e.nodeType is 1)) and (endPos < @caretPos)
          eString = ""
          if e.nodeType is 3
            eString = e.data
          else
            eString = e.text
          beginPos = endPos
          endPos = endPos + eString.length

          if endPos >= @caretPos
            front = eString.substring(0, @caretPos - beginPos)
            back = eString.substring(@caretPos - beginPos, eString.length)
            newContent = newContent.concat(front)
            newContent = newContent.concat(newTag)
            newContent = newContent.concat(back)
            return
          else
            newContent = newContent.concat(e)
            return
        else
          newContent = newContent.concat(e)
          return

    @questionBox.text ""
    $(newContent).each (i, e) =>
      @questionBox.append e

    that = this

    @questionBox.find('[rel*=blModal]').each (index, element) ->
      data = VideoClipper.getBLData $(element)

      startTime = VideoClipper.secondsToTime(data.startSeconds)
      endTime = VideoClipper.secondsToTime(data.endSeconds)

      $(element).click ->
        VideoClipper.modal.open this, that

      $(element).qtip
        style:
          classes: 'qtip-rounded qtip-dark'
        content:
          text: "Start: #{startTime} - End: #{endTime}"

    newVal = @questionBox.html()
    @questionBox.prev().val newVal

    return this

  ###
  Description: checks to see if the start and end time values in
    the snippet box are valid values
  params: N/A
  returns: true if the values are valid. false otherwise
  ###
  @checkErrors: =>
    startTime = parseFloat(@getStartTime())
    endTime = parseFloat(@getEndTime())
    if (startTime < endTime or isNaN(endTime)) and (not isNaN(startTime))
      $("input[name='bl-start']").removeClass "bl-incorrect"
      $("input[name='bl-end']").removeClass "bl-incorrect"
      true
    else
      $("input[name='bl-start']").addClass "bl-incorrect"
      $("input[name='bl-end']").addClass "bl-incorrect"
      false

  ###
  Description: resets the page's state to how it was 
    before VideoClipper was set up
  params: N/A
  returns: VideoClipper
  ###
  @cleanUp: =>
    $('#bl').remove()
    $('#bl-vid').remove()
    $("#bookMarklet-overlay").remove()
    @prepared.snippet = false
    for clipper in @clippers
      clipper.destroy()
    @clippers = []
    return this

  ###
  Description: sets the input boxes in the snippet box to empty strings
  params: N/A
  returns: VideoClipper
  ###
  @clearInputs: =>
    @setStartTime ""
    @setEndTime ""
    $("input[name='bl-start']").removeClass "bl-incorrect"
    $("input[name='bl-end']").removeClass "bl-incorrect"

    return this

  ###
  Description: Creates the neccessary html for VideoClipper
  params: N/A
  returns: VideoClipper
  ###
  @generate: (clipper)->
    @generateSnippetBox(clipper) if clipper?
    @generateVideoBox()
    @generateOverlay()

    that = this

    if !clipper?
      $('[rel*=blModal]').each (index, element) ->
        data = VideoClipper.getBLData $(element)

        startTime = VideoClipper.secondsToTime(data.startSeconds)
        endTime = VideoClipper.secondsToTime(data.endSeconds)

        $(element).click ->
          that.modal.open this

        $(element).qtip
          style:
            classes: 'qtip-rounded qtip-dark'
          content:
            text: "Start: #{startTime} - End: #{endTime}"

    return that

  ###
  Description: Creates a JSON string representing a clip's or snippet button's
    information.
  params: type - 'generate' or 'show'. 
    'generate' is for storing information necessary for the snippet button
    'show' is for storing the information necessary for the video clip
  params: clipper - an instance of VideoClipper to pull data from
  returns: a JSON string representing a clip's or snippet button's
  ###
  @generateBLDataString: (type, clipper) =>
    dataString = ""

    if type is "generate"
      dataString = """
        {
          \"elementId\": \"bl-player\",
          \"videoId\": \"#{clipper.videoId}\",
          \"videoType\": \"#{clipper.videoType}\",
          \"mediaContentUrl\": \"#{clipper.mediaContentUrl}\",
          \"thumbnailUrl\": \"#{clipper.thumbnailUrl}\",
          \"modal\": {
            \"Id\": \"bl\"
          }
        }
      """
    else if type is "show"
      dataString = """
      {
          \"elementId\": \"bl-playerV\",
          \"videoId\": \"#{clipper.videoId}\",
          \"videoType\": \"#{clipper.videoType}\",
          \"startSeconds\": \"#{clipper.startTime}\",
          \"endSeconds\": \"#{clipper.endTime}\",
          \"mediaContentUrl\": \"#{clipper.mediaContentUrl}\",
          \"thumbnailUrl\": \"#{clipper.thumbnailUrl}\",
          \"modal\": {
            \"Id\": \"bl-vid\"
          }
        }
      """    
    return dataString

  ###
  Description: Generates html for the modal window overlay
  params: N/A
  returns: VideoClipper
  ###
  @generateOverlay: =>
    $("<div id='bookMarklet-overlay'></div>").appendTo "body"  if $("#bookMarklet-overlay").length is 0
    $("#bookMarklet-overlay").click =>
      @modal.close()

    return this

  ###
  Description: Generates html and adds event handlers for the snippet box 
    which is display as a modal window
  params: clipper - A instance of VideoClipper to have event handlers added
  returns: VideoClipper
  ###
  @generateSnippetBox: (clipper) =>
    $("""
      <div id='bl'>
        <div class='bl-top'>
          <div class='bl-vid'>
            <div id='bl-player'></div>
          </div>
          <div class='bl-controls'>
            <div class='bl-title'>
              <h1>Create a Clip</h1>
            </div>
            <div class='bl-instructions'>
              By clicking the \"Start Time\" and \"End Time\" buttons or typing the time in the text boxes.
            </div>
            <table class='bl-input'>
              <tr>
                <td>
                  <input class='bl-button bl-start' type='button' value='Start Time'>
                </td>
                <td>
                </td>
                <td>
                  <input class='bl-button bl-end' type='button' value='End Time'>
                </td>
              </tr>
              <tr>
                <td>
                  <input class='bl-data' type='text' name='bl-start'>
                </td>
                <td>
                  -
                </td>
                <td>
                  <input class='bl-data' type='text' name='bl-end'>
                </td>
              </tr>
              <tr>
                <td>
                  <input class='bl-button bl-done' type='button' value='Done'>
                </td>
                <td>
                </td>
                <td>
                  <input class='bl-button bl-reset' type='button' value='Reset'>
                </td>
              </tr>
            </table>
          </div>
        </div>
        <div class='bl-bottom'>
          Source URL:<a class='bl-srcURL'></a>
        </div>
      </div>
      """).appendTo("body") if $("#bl").length is 0

    that = this
    
    clipper.questionBox.click (e) ->
      clipper.caretPos = clipper.getCaretPosition(this)
      return

    clipper.questionBox.keyup (e) ->
      clipper.caretPos = clipper.getCaretPosition(this)
      divText = $(this).html()
      $(this).prev().val divText
      return

    if !@prepared.snippet
      $(".bl-start").click (e) =>
        currTime = @player.getCurrentTime()
        that.setStartTime currTime
        that.checkErrors()
        return

      $(".bl-end").click (e) =>
        currTime = @player.getCurrentTime()
        that.setEndTime currTime
        that.checkErrors()
        return

      $(".bl-done").click (e) =>
        that.modal.close()
        that.clipper.update that.generateTag(that.clipper)
        return

      $(".bl-reset").click (e) =>
        VideoClipper.clearInputs()
        @player.cueVideoById 
          videoId: that.clipper.videoId
          startSeconds: 0
          suggestedQuality: "large"
        return

      @prepared.snippet = true

    return this

  ###
  Description: Generates a new a tag that represents a video clip
  params: clipper - a VideoClipper instance to pull data from
  returns: a string containing a video clip a tag if the data is valid.
    If the data isn't valid, an empty string is returned.
  ###
  @generateTag: (clipper) =>

    # Get in and out points
    clipper.startTime = @getStartTime()
    clipper.endTime = @getEndTime()

    # Check for errors and proceed
    if VideoClipper.checkErrors()

      # Default for endTime is an empty string
      clipper.endTime = @player.getDuration() if isNaN parseFloat clipper.endTime 

      # Generate an anchor tag with encoded JSON as text
      newTag = ""
      dataString = @generateBLDataString "show", clipper
      # Logging for edX
      # Logger.log('video_clip', $.parseJSON(dataString));
      blDataEncoded = encodeURI(dataString)
      newTag = $("<a rel='blModal' href='#bl-vid' class='bl'>"+ blDataEncoded+ "</a>").css
        'background-image': clipper.reel

      that = this

      clipper.clips = clipper.clips.concat(newTag)

      return newTag
    else
      return ""

  ###
  Description: Generates the html for the video box modal window
    if it doesn't exist
  params: N/A
  returns: VideoClipper
  ###
  @generateVideoBox: =>
    $("""
      <div id='bl-vid'>
        <div class='bl-video-wrap'>
          <div id='bl-playerV'></div>
        </div>
      </div>
      """).appendTo("body") if $("#bl-vid").length is 0

    return this

  ###
  Description: Gets the clip or snippt button information from an element
  params: el - the element to retrieve the data from.
  returns: If it is a valid element, an object containing 
    the information is returned. Otherwise undefined is returned.
  ###
  @getBLData: (el) =>
    blData = undefined
    if typeof ($(el).attr("data-bl")) isnt "undefined"
      blData = $.parseJSON(decodeURI($(el).attr("data-bl")))
    else blData = $.parseJSON(decodeURI($(el).text()))  if typeof ($(el).text()) isnt "undefined"
    return blData

  ###
  Description: An object representing the VideoClipper's modal window
  ###
  @modal:

    ###
    Description: element to be displayed as a model window.
    ###
    Id: "" # bl or bl-vid
    
    ###
    Description: Closes the currently open modal window
    params: modalId (optional) - id for the modal window to be closed
    returns: VideoClipper
    ###
    close: (modalId) =>
      modalId = modalId or @modal.Id
      $("#bookMarklet-overlay").fadeOut 200
      $("##{modalId}").css display: "none"
      if modalId is "bl"
        VideoClipper.player.stopVideo()
      else 
        VideoClipper.playerV.stopVideo()  if modalId is "bl-vid"
      return VideoClipper  

    ###
    Description: Opens a VideoClipper modal window
    params: element - element to get the video information from.
    params: clipper (optional) - A instance of VideoClipper
      used for opening the snippet box
    returns: VideoClipper
    ###
    open: (element, clipper) =>
      that = this
      @modal.close()
      blData = @getBLData(element)
      @clipper = clipper

      if blData.modal.Id is "bl"
        clipper.videoId = blData.videoId
        clipper.videoType = blData.videoType

        url = ""
        url = "http://www.youtube.com/embed/" + clipper.videoId  if clipper.videoType is "YT"
        $(".bl-srcURL").attr "href", url
        $(".bl-srcURL").text url

        @clearInputs()
        if @player is false || @player.videoType != blData.videoType || @playerV.videoId == blData.videoId
          @player.remove() if @player? && @player
          @player = new OmniPlayer blData
        else
          @player.cueVideoById(blData)
      else
        # OPTIMIZE: This works, 
        #   but it would be nice if it didn't need to delete the video
        if @playerV is false || @playerV.videoType != blData.videoType || @playerV.videoId == blData.videoId
          @playerV.remove() if @playerV? && @playerV
          @playerV = new OmniPlayer blData
        else
          @playerV.cueVideoById blData

      @modal.Id = blData.modal.Id

      modalWidth = $("##{@modal.Id}").outerWidth()
      $("#bookMarklet-overlay").css
        display: "block"
        opacity: 0

      $("#bookMarklet-overlay").fadeTo 200, 0.5
      $("##{@modal.Id}").css
        display: "block"
        position: "fixed"
        opacity: 0
        "z-index": 11000
        left: 50 + "%"
        "margin-left": -(modalWidth / 2) + "px"
        top: "100px"

      $("##{@modal.Id}").fadeTo 200, 1

      return VideoClipper

  ###
  Description: reformats html from a string
  params: html - A string of html
  returns: proper html string
  ###
  @stripHTML: (html) ->
    tmp = document.createElement("DIV")
    tmp.innerHTML = html
    tmp.textContent or tmp.innerText

  ###
  Description: Turns a string or float of seconds into a formatted time string.
    The format is HH:MM:SS, MM:SS or SS depending on magnitude
  params: seconds - String or float of seconds
  returns: a time string
  ###
  @secondsToTime: (seconds) ->
    if seconds == ""
      return seconds
    else
      seconds = parseFloat(seconds).toFixed(2)

      hours = parseInt(seconds / 3600)
      minutes = parseInt(seconds / 60) % 60
      seconds = parseFloat(seconds % 60).toFixed(2)
      result = ""

      if hours > 0
        minutes = "0#{minutes}" if (minutes / 10) < 1
        seconds = "0#{seconds}" if (seconds / 10) < 1
        result = "#{hours}:#{minutes}:#{seconds}"
      else if minutes > 0
        seconds = "0#{seconds}" if (seconds / 10) < 1
        result = "#{minutes}:#{seconds}"
      else
        result = "#{seconds}"

      return result

  ###
  Description: Turns a time string into a number of seconds
  params: time - A string representing time
  returns: a float representing a number of seconds
  ###
  @timeToSeconds: (time) ->
    amounts = time.split(':')
    seconds = 0

    len = amounts.length
    for amount, index in amounts
      seconds += parseFloat(amount)*Math.pow(60, len-(index+1))

    return seconds.toFixed(2)

  ###
  Description: Gets the end time from the snippet box
  params: N/A
  returns: a float representing the number of seconds to the end point
  ###
  @getEndTime: ->
    val = $("input[name='bl-end']").val() 
    return @timeToSeconds(val)

  ###
  Description: Gets the start time from the snippet box
  params: N/A
  returns: a float representing the number of seconds to the start point
  ###
  @getStartTime: ->
    val = $("input[name='bl-start']").val()
    return @timeToSeconds(val)

  ###
  Description: Sets the end time in the snippet box
  params: val - Number of seconds
  returns: the val as a time string
  ###
  @setEndTime: (val) ->
    val = @secondsToTime val
    $("input[name='bl-end']").val val
    return val

  ###
  Description: Sets the start time in the snippet box
  params: val - Number of seconds
  returns: the val as a time string
  ###
  @setStartTime: (val) ->
    val = @secondsToTime val
    $("input[name='bl-start']").val val
    return val

VideoClipper.generate()
if window.onVideoClipperReady?
  VideoClipper.callback = true
  window.onVideoClipperReady()

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

    OmniPlayer["_#{@videoType}"].createPlayer.apply(this, [obj])

  ###
  Description: The following 7 functions are based on the YouTube API and
    are required for the VideoClipper to work.
    They need to be implemented by the players within Omniplayer.
  ###
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

  @_JW:
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

      OmniPlayer._JW.setup.apply this, [false]

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

        OmniPlayer._JW.setup.apply this, [false]

      @cueVideoById = (options) ->
        @internal.remove() if @internal?

        @endSeconds = options.endSeconds
        @startSeconds = options.startSeconds
        @videoId = options.videoId

        OmniPlayer._JW.setup.apply this, [false]


      @loadVideoById = (options) ->
        @internal.remove() if @internal?

        @endSeconds = options.endSeconds
        @startSeconds = options.startSeconds
        @videoId = options.videoId

        OmniPlayer._JW.setup.apply this, [true]

      @loadVideoByUrl = (options) ->
        @internal.remove() if @internal?

        @endSeconds = options.endSeconds
        @startSeconds = options.startSeconds
        @mediaContentUrl = options.mediaContentUrl
        @thumbnailUrl = options.thumbnailUrl

        OmniPlayer._JW.setup.apply this, [true]

      @remove = ->
        @internal.remove()

    createPlayer: (obj) ->
      if jwplayer.key?
        OmniPlayer._JW.build.apply this, [obj]
        OmniPlayer.loaded.JW = true
      else
        throw new Error 'jwplayer.key is not defined'

  @_YT: 
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
        OmniPlayer._YT.build.apply this
      else
        window.onYouTubeIframeAPIReady = () ->
          OmniPlayer.loaded.YT = true
          OmniPlayer._YT.build.apply that

        OmniPlayer._YT.setup()

  @_TEST:
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
