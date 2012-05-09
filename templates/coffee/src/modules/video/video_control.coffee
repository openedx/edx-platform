class VideoControl
  constructor: (@player) ->
    @render()
    @bind()

  $: (selector) ->
    @player.$(selector)

  bind: ->
    $(@player).bind('play', @onPlay)
      .bind('pause', @onPause)
      .bind('ended', @onPause)
    @$('.video_control').click @togglePlayback

  render: ->
    @$('.video-controls').append """
      <div class="slider"></div>
      <div>
        <ul class="vcr">
          <li><a class="video_control play">Play</a></li>
          <li>
            <div class="vidtime">0:00 / 0:00</div>
          </li>
        </ul>
        <div class="secondary-controls">
          <a href="#" class="add-fullscreen" title="Fill browser">Fill Browser</a>
        </div>
      </div>
     """

  onPlay: =>
    @$('.video_control').removeClass('play').addClass('pause').html('Pause')

  onPause: =>
    @$('.video_control').removeClass('pause').addClass('play').html('Play')

  togglePlayback: (event) =>
    event.preventDefault()
    if $(event.target).hasClass('play')
      $(@player).trigger('play')
    else
      $(@player).trigger('pause')
