class @VideoCaption
  constructor: (@player, @youtubeId) ->
    @render()
    @bind()

  $: (selector) ->
    @player.$(selector)

  bind: ->
    $(window).bind('resize', @onWindowResize)
    $(@player).bind('resize', @onWindowResize)
    $(@player).bind('updatePlayTime', @onUpdatePlayTime)
    $(@player).bind('play', @onPlay)
    @$('.hide-subtitles').click @toggle
    @$('.subtitles').mouseenter(@onMouseEnter).mouseleave(@onMouseLeave)
      .mousemove(@onMovement).bind('mousewheel', @onMovement)
      .bind('DOMMouseScroll', @onMovement)

  captionURL: ->
    "http://www.universalsubtitles.org/api/1.0/subtitles/?video_url=http://www.youtube.com/watch?v=69rDtSpshAw"
    # "/static/subs/#{@youtubeId}.srt.sjson"

  render: ->
    @$('.video-wrapper').after """
      <ol class="subtitles"><li>Attempting to load captions...</li></ol>
      """
    @$('.video-controls .secondary-controls').append """
      <a href="#" class="hide-subtitles" title="Turn off captions">Captions</a>
      """
    @$('.subtitles').css maxHeight: @$('.video-wrapper').height() - 5
    @fetchCaption()

  fetchCaption: ->
    $.ajax
      dataType: 'jsonp' 
      url: @captionURL()
      success: (captions) =>
        # We take the captions that are each in a dictionary with a key,
        # and create two arrays. One with all the start times, and one with
        # all the texts. Their indices correspond.
        @captions = []
        @start = []
        record = (single_caption) =>
          @captions.push single_caption.text
          @start.push single_caption.start_time * 1000
        record single_caption for single_caption in captions
        if onTouchBasedDevice()
          $('.subtitles li').html "Caption will be displayed when you start playing the video."
        else
          @renderCaption()
        
  renderCaption: ->
    container = $('<ol>')

    $.each @captions, (index, text) =>
      container.append $('<li>').html(text).attr
        'data-index': index
        'data-start': @start[index]

    @$('.subtitles').html(container.html())
    @$('.subtitles li[data-index]').click @seekPlayer

    # prepend and append an empty <li> for cosmatic reason
    @$('.subtitles').prepend($('<li class="spacing">').height(@topSpacingHeight()))
      .append($('<li class="spacing">').height(@bottomSpacingHeight()))

    @rendered = true

  search: (time) ->
    min = 0
    max = @start.length - 1
    
    while min < max
      index = Math.ceil((max + min) / 2)
      if time < @start[index]
        max = index - 1
      if time >= @start[index]
        min = index

    return min

  onPlay: =>
    @renderCaption() unless @rendered

  onUpdatePlayTime: (event, time) =>
    # This 250ms offset is required to match the video speed
    time = Math.round(Time.convert(time, @player.currentSpeed(), '1.0') * 1000 + 250)
    newIndex = @search time

    if newIndex != undefined && @currentIndex != newIndex
      if @currentIndex
        @$(".subtitles li.current").removeClass('current')
      @$(".subtitles li[data-index='#{newIndex}']").addClass('current')

      @currentIndex = newIndex
      @scrollCaption()

  onWindowResize: =>
    @$('.subtitles').css maxHeight: @captionHeight()
    @$('.subtitles .spacing:first').height(@topSpacingHeight())
    @$('.subtitles .spacing:last').height(@bottomSpacingHeight())
    @scrollCaption()

  onMouseEnter: =>
    clearTimeout @frozen if @frozen
    @frozen = setTimeout @onMouseLeave, 10000

  onMovement: =>
    @onMouseEnter()

  onMouseLeave: =>
    clearTimeout @frozen if @frozen
    @frozen = null
    @scrollCaption() if @player.isPlaying()

  scrollCaption: ->
    if !@frozen && @$('.subtitles .current:first').length
      @$('.subtitles').scrollTo @$('.subtitles .current:first'),
        offset: - @calculateOffset(@$('.subtitles .current:first'))

  seekPlayer: (event) =>
    event.preventDefault()
    time = Math.round(Time.convert($(event.target).data('start'), '1.0', @player.currentSpeed()) / 1000)
    $(@player).trigger('seek', time)

  calculateOffset: (element) ->
    @captionHeight() / 2 - element.height() / 2

  topSpacingHeight: ->
    @calculateOffset(@$('.subtitles li:not(.spacing):first'))

  bottomSpacingHeight: ->
    @calculateOffset(@$('.subtitles li:not(.spacing):last'))

  toggle: (event) =>
    event.preventDefault()
    if @player.element.hasClass('closed')
      @$('.hide-subtitles').attr('title', 'Turn off captions')
      @player.element.removeClass('closed')
      @scrollCaption()
    else
      @$('.hide-subtitles').attr('title', 'Turn on captions')
      @player.element.addClass('closed')

  captionHeight: ->
    if @player.element.hasClass('fullscreen')
      $(window).height() - @$('.video-controls').height()
    else
      @$('.video-wrapper').height()
