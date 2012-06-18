class @VideoVolumeControl
  constructor: (@player) ->
    @previousVolume = 100
    @render()
    @bind()

  $: (selector) ->
    @player.$(selector)

  bind: ->
    $(@player).bind('ready', @onReady)
    @$('.volume').mouseenter ->
      $(this).addClass('open')
    @$('.volume').mouseleave ->
      $(this).removeClass('open')
    @$('.volume>a').click(@toggleMute)

  render: ->
    @$('.secondary-controls').prepend """
      <div class="volume">
        <a href="#"></a>
        <div class="volume-slider-container">
          <div class="volume-slider"></div>
        </div>
      </div>
      """
    @slider = @$('.volume-slider').slider
      orientation: "vertical"
      range: "min"
      min: 0
      max: 100
      value: 100
      change: @onChange
      slide: @onChange

  onReady: =>
    @slider.slider 'option', 'max', @player.volume()

  onChange: (event, ui) =>
    @player.volume ui.value
    @$('.secondary-controls .volume').toggleClass 'muted', ui.value == 0

  toggleMute: =>
    if @player.volume() > 0
      @previousVolume = @player.volume()
      @slider.slider 'option', 'value', 0
    else
      @slider.slider 'option', 'value', @previousVolume
