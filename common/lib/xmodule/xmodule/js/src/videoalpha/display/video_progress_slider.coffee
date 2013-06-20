class @VideoProgressSliderAlpha extends SubviewAlpha
  initialize: ->
    @buildSlider() unless onTouchBasedDevice()

  buildSlider: ->
    @slider = @el.slider
      range: 'min'
      change: @onChange

      slide: @onSlide
      stop: @onStop
    @buildHandle()

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

  play: =>
    @buildSlider() unless @slider

  updatePlayTime: (currentTime, duration) ->
    if @slider && !@frozen
      @slider.slider('option', 'max', duration)
      @slider.slider('value', currentTime)

  onSlide: (event, ui) =>
    @frozen = true
    @updateTooltip(ui.value)
    $(@).trigger('slide_seek', ui.value)

  onChange: (event, ui) =>
    @updateTooltip(ui.value)

  onStop: (event, ui) =>
    @frozen = true
    $(@).trigger('slide_seek', ui.value)
    setTimeout (=> @frozen = false), 200

  updateTooltip: (value)->
    @handle.qtip('option', 'content.text', "#{Time.format(value)}")
