class @VideoVolumeControl extends Subview
  initialize: ->
    @currentVolume = 100

  bind: ->
    @$('.volume').mouseenter ->
      $(this).addClass('open')
    @$('.volume').mouseleave ->
      $(this).removeClass('open')
    @$('.volume>a').click(@toggleMute)

  render: ->
    @el.prepend """
      <div class="volume">
        <a href="#"></a>
        <div class="volume-slider-container">
          <div class="volume-slider"></div>
        </div>
      </div>
      """#"
    @slider = @$('.volume-slider').slider
      orientation: "vertical"
      range: "min"
      min: 0
      max: 100
      value: 100
      change: @onChange
      slide: @onChange

  onChange: (event, ui) =>
    @currentVolume = ui.value
    $(@).trigger 'volumeChange', @currentVolume
    @$('.volume').toggleClass 'muted', @currentVolume == 0

  toggleMute: =>
    if @currentVolume > 0
      @previousVolume = @currentVolume
      @slider.slider 'option', 'value', 0
    else
      @slider.slider 'option', 'value', @previousVolume
