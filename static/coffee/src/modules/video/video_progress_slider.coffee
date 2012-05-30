class @VideoProgressSlider
  constructor: (@player) ->
    @buildSlider()
    @buildHandle()
    $(@player).bind('updatePlayTime', @onUpdatePlayTime)
    $(@player).bind('ready', @onReady)

  $: (selector) ->
    @player.$(selector)

  buildSlider: ->
    @slider = @$('.slider').slider
      range: 'min'
      change: @onChange
      slide: @onSlide
      stop: @onStop

  buildHandle: ->
    @handle = @$('.ui-slider-handle')
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

  onReady: =>
    @slider.slider('option', 'max', @player.duration())

  onUpdatePlayTime: (event, currentTime) =>
    if !@frozen
      @slider.slider('option', 'max', @player.duration())
      @slider.slider('value', currentTime)

  onSlide: (event, ui) =>
    @frozen = true
    @updateTooltip(ui.value)
    $(@player).trigger('seek', ui.value)

  onChange: (event, ui) =>
    @updateTooltip(ui.value)

  onStop: (event, ui) =>
    @frozen = true
    $(@player).trigger('seek', ui.value)
    setTimeout (=> @frozen = false), 200

  updateTooltip: (value)->
    @handle.qtip('option', 'content.text', "#{Time.format(value)}")
