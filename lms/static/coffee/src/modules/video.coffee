class @Video
  constructor: (@id, videos) ->
    window.player = null

    @element = $("#video_#{@id}")
    @element.data('video', this)

    @media = @element.find('video').first()
    @sources = @media.find('sources')
    @controls = @element.find('.video-controls')

    @render()

  render: ->
    new MediaSliderControl @
    new MediaPlayControl @
    new MediaTimeDisplay @
    new MediaSpeedControl @, [0.75, 1.0, 1.25, 1.50]
    new MediaVolumeControl @ unless onTouchBasedDevice()
    new MediaFullscreenControl @
