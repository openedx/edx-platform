class @VideoQualityControlAlpha extends SubviewAlpha
  initialize: ->
    @quality = null;

  bind: ->
    @$('.quality_control').click @toggleQuality

  render: ->
    @el.append """
      <a href="#" class="quality_control" title="HD">HD</a>
      """#"

  onQualityChange: (value) ->
    @quality = value
    if @quality in ['hd720', 'hd1080', 'highres']
        @el.addClass('active')
    else
        @el.removeClass('active')

  toggleQuality: (event) =>
    event.preventDefault()
    if @quality in ['hd720', 'hd1080', 'highres']
        newQuality = 'large'
    else
        newQuality = 'hd720'
    $(@).trigger('changeQuality', newQuality)