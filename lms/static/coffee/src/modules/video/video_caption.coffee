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
    @$('.caption-menu').click @toggleLanguageMenu

  captionURL: ->
    "http://www.universalsubtitles.org/api/1.0/subtitles/"
    # "/static/subs/#{@youtubeId}.srt.sjson"
  languagesURL: ->
    "http://www.universalsubtitles.org/api/1.0/subtitles/languages/"
    
  getLanguageCode: ->
    if not @_languageCode?
      cookied = $.cookie("video_caption_language_code")
      @_languageCode = if cookied? cookied else "en"
          
    return @_languageCode
    
  setLanguageCode: (newCode) ->
    @_languageCode = newCode
    $.cookie('video_caption_language_code', "#{newCode}", expires: 3650, path: '/')
    @fetchCaptions()

  render: ->
    @$('.video-wrapper').after """
      <ol class="subtitles"><li>Attempting to load captions...</li></ol>
      """
    @$('.video-controls .secondary-controls').append """
      <a href="#" class="hide-subtitles" title="Turn off captions">Captions</a>
      """
    @$('.subtitles').css maxHeight: @$('.video-wrapper').height() - 5
    @$('.subtitles').before """
      <a href="#" class="caption-menu">English</a>
      """
    @language_menu = $("""
      <div class="language-menu">
        <ol class="language-list"></ol>
        <div class="caption-links">
          <a href="#">Caption This Video</a>
        </div>
      </div>
      """).hide()
    $('body').append(@language_menu)
    @fetchCaptions()
    @fetchLanguages()
    
  fetchLanguages: ->
    $.ajax
      dataType: 'jsonp' 
      url: @languagesURL()
      data:
        video_url: 'http://www.youtube.com/watch?v=69rDtSpshAw'
      success: (languages) =>
        # We put the available languages into 
        @languages = languages
        @renderLanguagesMenu()
  
  fetchCaptions: ->
    $.ajax
      dataType: 'jsonp' 
      url: @captionURL()
      data:
        video_url: 'http://www.youtube.com/watch?v=69rDtSpshAw'
        language: @getLanguageCode()
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

  renderLanguagesMenu: ->
    list = $("<ol>")
    
    $.each @languages, (index, language) =>
      # Would string concatenation be faster here?
      element = $('<li>')
        .attr
          'data-language-code' : language.code
        .append(
          $('<span>').text(language.name),
          $('<span>').text(language.completion)
        )
          
      list.append element
    
    language_list = $(".language-list", @language_menu)
    language_list.html( list.html() )
    
    $('.language-list li[data-language-code]', @language_menu).click @selectLanguage
  
  toggleLanguageMenu: (event) =>
    event.preventDefault()
    if @language_menu.is(":hidden")
      pos = @$('.caption-menu').offset()
      height = @$('.caption-menu').outerHeight()
    
      @language_menu.css
        position: "absolute"
        top: (pos.top + height) + "px"
        left: pos.left + "px"
      .show();
    else
      @language_menu.hide()
      
  selectLanguage: (event) =>
    language_code = $(event.currentTarget).data('language-code')
    @setLanguageCode(language_code)
    

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
