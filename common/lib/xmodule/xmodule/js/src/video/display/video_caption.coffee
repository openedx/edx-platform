class @VideoCaption extends Subview
  initialize: ->
    @loaded = false  

  bind: ->
    $(window).bind('resize', @resize)
    @$('.hide-subtitles').click @toggle
    @$('.subtitles').mouseenter(@onMouseEnter).mouseleave(@onMouseLeave)
      .mousemove(@onMovement).bind('mousewheel', @onMovement)
      .bind('DOMMouseScroll', @onMovement)

  captionURL: ->
    "/static/#{@captionDataDir}/subs/#{@youtubeId}.srt.sjson"

  render: ->
    # TODO: make it so you can have a video with no captions.
    #@$('.video-wrapper').after """
    #  <ol class="subtitles"><li>Attempting to load captions...</li></ol>
    #  """
    @$('.video-wrapper').after """
      <ol class="subtitles"></ol>
      """
    @$('.video-controls .secondary-controls').append """
      <a href="#" class="hide-subtitles" title="Turn off captions">Captions</a>
      """
    @$('.subtitles').css maxHeight: @$('.video-wrapper').height() - 5
    @fetchCaption()

  fetchCaption: ->
    $.getWithPrefix @captionURL(), (captions) =>
      @captions = captions.text
      @start = captions.start

      @loaded = true

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
    if @loaded
      min = 0
      max = @start.length - 1

      while min < max
        index = Math.ceil((max + min) / 2)
        if time < @start[index]
          max = index - 1
        if time >= @start[index]
          min = index
      return min

  play: ->
    if @loaded
      @renderCaption() unless @rendered
      @playing = true

  pause: ->
    if @loaded
      @playing = false

  updatePlayTime: (time) ->
    if @loaded
      # This 250ms offset is required to match the video speed
      time = Math.round(Time.convert(time, @currentSpeed, '1.0') * 1000 + 250)
      newIndex = @search time

      if newIndex != undefined && @currentIndex != newIndex
        if @currentIndex
          @$(".subtitles li.current").removeClass('current')
        @$(".subtitles li[data-index='#{newIndex}']").addClass('current')

        @currentIndex = newIndex
        @scrollCaption()

  resize: =>
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
    @scrollCaption() if @playing

  scrollCaption: ->
    if !@frozen && @$('.subtitles .current:first').length
      @$('.subtitles').scrollTo @$('.subtitles .current:first'),
        offset: - @calculateOffset(@$('.subtitles .current:first'))

  seekPlayer: (event) =>
    event.preventDefault()
    time = Math.round(Time.convert($(event.target).data('start'), '1.0', @currentSpeed) / 1000)
    $(@).trigger('seek', time)

  calculateOffset: (element) ->
    @captionHeight() / 2 - element.height() / 2

  topSpacingHeight: ->
    @calculateOffset(@$('.subtitles li:not(.spacing):first'))

  bottomSpacingHeight: ->
    @calculateOffset(@$('.subtitles li:not(.spacing):last'))

  toggle: (event) =>
    event.preventDefault()
    if @el.hasClass('closed')
      @$('.hide-subtitles').attr('title', 'Turn off captions')
      @el.removeClass('closed')
      @scrollCaption()
    else
      @$('.hide-subtitles').attr('title', 'Turn on captions')
      @el.addClass('closed')

  captionHeight: ->
    if @el.hasClass('fullscreen')
      $(window).height() - @$('.video-controls').height()
    else
      @$('.video-wrapper').height()
