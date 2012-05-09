class VideoCaption
  constructor: (@player, @youtubeId) ->
    @index = []
    @render()
    @bind()

  $: (selector) ->
    @player.$(selector)

  bind: ->
    $(window).bind('resize', @onWindowResize)
    $(@player).bind('resize', @onWindowResize)
    $(@player).bind('updatePlayTime', @onUpdatePlayTime)
    @$('.hide-subtitles').click @toggle
    @$('.subtitles').mouseenter(@onMouseEnter).mouseleave(@onMouseLeave)
      .mousemove(@onMovement).bind('mousewheel', @onMovement)
      .bind('DOMMouseScroll', @onMovement)

  captionURL: ->
    "/static/subs/#{@youtubeId}.srt.sjson"

  render: ->
    @$('.video-wrapper').after """
      <ol class="subtitles"><li>Attempting to load captions...</li></ol>
      """
    @$('.video-controls .secondary-controls').append """
      <a href="#" class="hide-subtitles" title="Turn off captions">Captions</a>
      """
    @$('.subtitles').css maxHeight: @$('.video-wrapper').height() - 5
    @fetchCaption()

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

  fetchCaption: ->
    $.getJSON @captionURL(), (captions) =>
      @captions = captions.text
      @start = captions.start
      for index in [0...captions.start.length]
        for time in [captions.start[index]..captions.end[index]]
          @index[time] ||= []
          @index[time].push(index)
      @renderCaption()

  onUpdatePlayTime: (event, time) =>
    # This 250ms offset is required to match the video speed
    time = Math.round(Time.convert(time, @player.currentSpeed(), '1.0') * 1000 + 250)
    newIndex = @index[time]

    if newIndex != undefined && @currentIndex != newIndex
      if @currentIndex
        for index in @currentIndex
          @$(".subtitles li[data-index='#{index}']").removeClass('current')

      for index in newIndex
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

  onMovement: (event) =>
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
    @calculateOffset(@$('.subtitles li:not(.spacing).first'))

  bottomSpacingHeight: ->
    @calculateOffset(@$('.subtitles li:not(.spacing).last'))

  toggle: (event) =>
    event.preventDefault()
    if @player.element.hasClass('closed')
      @$('.hide-subtitles').attr('title', 'Turn off captions')
      @player.element.removeClass('closed')
    else
      @$('.hide-subtitles').attr('title', 'Turn on captions')
      @player.element.addClass('closed')
    @scrollCaption()

  captionHeight: ->
    if @player.element.hasClass('fullscreen')
      $(window).height() - @$('.video-controls').height()
    else
      @$('.video-wrapper').height()

