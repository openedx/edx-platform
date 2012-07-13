class @MediaControl
  constructor: (@container, args...) ->
    @media = @container.media
    @controls = @container.controls

    @initialize(args...)
    @render()
    @bind()

  get_vcr_controls: ->
    if not @_vcr_controls
      @_vcr_controls = @controls.find('.vcr').first()
      if @_vcr_controls.length == 0
        @_vcr_controls = $('<ul class="vcr">')
        @controls.append($('<div>').append(@_vcr_controls))
    return @_vcr_controls

  get_secondary_controls: ->
    if not @_secondary_controls
      @_secondary_controls = @controls.find('.secondary-controls').first()
      if @_secondary_controls.length == 0
        @_secondary_controls = $('<div class="secondary-controls">')
        @controls.append(@_secondary_controls)
    return @_secondary_controls

  initialize:->
  bind: ->
  render:->


class @MediaPlayControl extends @MediaControl
  render: ->
    @element = $('<a class="video_control"  href="#"></a>')

    @get_vcr_controls().append($('<li>').append(@element))

    unless onTouchBasedDevice()
      @element.addClass('play').html('Play')

  bind: ->
    @media.bind('play', @onPlay)
      .bind('pause', @onPause)
      .bind('ended', @onPause)
    @element.click(@togglePlayback)

  onPlay: =>
    @element.removeClass('play').addClass('pause').html('Pause')

  onPause: =>
    @element.removeClass('pause').addClass('play').html('Play')

  togglePlayback: (event) =>
    event.preventDefault()
    if @element.hasClass('play') || @element.hasClass('pause')
      if @media[0].paused
        @media.trigger('play')
      else
        @media.trigger('pause')


class @MediaTimeDisplay extends @MediaControl
  render: ->
    @element = $('<div class="vidtime">0:00 / 0:00</div>')

    @get_vcr_controls().append($('<li>').append(@element))

  bind: ->
     @media.bind('timeupdate', @onTimeUpdate)

  onTimeUpdate: (event) =>
    media = @media[0]
    progress = Time.format(media.currentTime) + ' / ' + Time.format(media.duration)
    @element.html(progress)


class @MediaFullscreenControl extends @MediaControl
  initialize: () ->
    @parent = @container.element

  render: ->
    @element = $('<a href="#" class="add-fullscreen" title="Fullscreen">Fullscreen</a>')

    @get_secondary_controls().append(@element)

  bind: ->
    $(document).keyup(@exitFullScreen)
    @element.click(@toggleFullScreen)

  toggleFullScreen: (event) =>
    event.preventDefault()

    if not @container.element.hasClass('fullscreen')
      @element.attr('title', 'Exit fill browser')

      @parent.append('<a href="#" class="exit">Exit</a>').click(@exitFullScreen)
      @parent.addClass('fullscreen')
    else
      @element.attr('title', 'Fullscreen')

      @parent.find('.exit').remove()
      @parent.removeClass('fullscreen')

    @parent.resize()

  exitFullScreen: (event) =>
    if @parent.hasClass('fullscreen') && event.keyCode == 27
      @toggleFullScreen(event)


class @MediaSliderControl extends @MediaControl
  initialize: ->
    # slider scale factor. used to make the motion of the slider's
    # handle smoother for short movies.
    @_ssf = 100

  render: ->
    @element = $('<div class="slider"></div>')
    @controls.append(@element)
    @render_slider() unless onTouchBasedDevice()

  render_slider: ->
    @slider = @element.slider
      range: 'min'
      change: @onChange
      slide: @onSlide
      stop: @onStop

    @handle = @slider.find('.ui-slider-handle')
    @handle.qtip
      content: "#{Time.format(@slider.slider('value'))}"
      position:
        my: 'bottom center'
        at: 'top center'
        container: @handle
      hide:
        delay: 700
      style:
        classes: 'ui-tooltip-slider'
        widget: true

  bind: ->
    @media.bind('loadedmetadata', @onLoadedMetadata)
      .bind('play', @onPlay)
      .bind('timeupdate', @onTimeUpdate)

  seek: (value) ->
    time = value / @_ssf
    @media[0].currentTime = time

  updateTooltip: (value)->
    value = value / @_ssf
    @handle.qtip('option', 'content.text', "#{Time.format(value)}")

  onLoadedMetadata: =>
    max_value =  @_ssf * @media[0].duration
    @slider.slider('option', 'max', max_value) if @slider

  onPlay: =>
    if not @slider
      render_slider

  onTimeUpdate: =>
    if @slider and not @sliding
        max_value =  @_ssf * @media[0].duration
        @slider.slider('option', 'max', max_value)

        pos_value =  @_ssf * @media[0].currentTime
        @slider.slider('value', pos_value)

  onChange: (event, ui) =>
    @updateTooltip(ui.value)

  onSlide: (event, ui) =>
    @sliding = true
    @seek(ui.value)
    @updateTooltip(ui.value)

  onStop: (event, ui) =>
    @sliding = false
    @seek(ui.value)


class @MediaVolumeControl extends @MediaControl
  initialize: ->
    @previousVolume = 100

  render: ->
    @element = $('<div class="volume"><a href="#"></a></div>')
    @volume = $('<div class="volume-slider">')
    @element.append(
      $('<div class="volume-slider-container">').append(@volume))

    @get_secondary_controls().append(@element)

    @render_slider() unless onTouchBasedDevice()

  render_slider: ->
   @slider = @volume.slider
      orientation: "vertical"
      range: "min"
      min: 0
      max: 100
      value: 100
      change: @onChange
      slide: @onChange

  bind: ->
    @media.bind('canplay', @onCanPlay)
    @element.mouseenter =>
      @element.addClass('open')
    @element.mouseleave =>
      @element.removeClass('open')
    @element.find('>a').click(@toggleMute)

  onCanPlay: =>
    @slider.slider('option', 'max', 100 * @media[0].volume)

  onChange:(event, ui) =>
    @media[0].volume = ui.value / 100
    @element.toggleClass('muted', ui.value == 0)

  toggleMute: =>
    media = @media[0]
    if media.volume > 0
      @previousVolume = 100 * media.volume
      @slider.slider('option', 'value', 0)
    else
      @slider.slider('option', 'value', @previousVolume)


class @MediaSpeedControl extends @MediaControl
  initialize: (@speeds) ->

  render: ->
    @element = $("""
      <div class="speeds">
        <a href="#">
          <h3>Speed</h3>
          <p class="active"></p>
        </a>
      </div>
      """) #"

    @selector = $('<ol class="video_speeds">')
    @element.append(@selector)

    $.each @speeds, (index, speed) =>
      link = $('<a>').attr(href: "#").html("#{speed}x")
      @selector.prepend($('<li>').attr('data-speed', speed).append(link))

    @get_secondary_controls().append(@element)

    @setSpeed(@media[0].defaultPlaybackRate)

  bind: ->
    @media.bind('ratechange', @onSpeedChange)
    @selector.find('a').click(@changeVideoSpeed)
    if onTouchBasedDevice()
      @element.click (event) ->
        event.preventDefault()
        $(this).toggleClass('open')
    else
      @element.mouseenter ->
        $(this).addClass('open')
      @element.mouseleave ->
        $(this).removeClass('open')
      @element.click (event) ->
        event.preventDefault()
        $(this).toggleClass('open')

  setSpeed: (speed) ->
    @selector.find('li').removeClass('active')
    @selector.find("li[data-speed='#{speed}']").addClass('active')
    @selector.find('p.active').html("#{speed}x")

  changeVideoSpeed: (event) =>
    event.preventDefault()
    unless $(event.target).parent().hasClass('active')
      @media[0].playbackRate = $(event.target).parent().data('speed')

  onSpeedChange: (event) =>
    speed = @media[0].playbackRate
    value  = parseFloat(speed).toFixed(2).replace(/\.00$/, '.0')
    @setSpeed(value)
