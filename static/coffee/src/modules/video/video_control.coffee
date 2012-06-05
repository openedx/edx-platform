class @VideoControl
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
          <li><a class="video_control" href="#"></a></li>
          <li>
            <div class="vidtime">0:00 / 0:00</div>
          </li>
        </ul>
        <div class="secondary-controls">
          <a href="#" class="add-fullscreen" title="Fill browser">Fill Browser</a>
        </div>
      </div>
      """

    unless onTouchBasedDevice()
      @$('.video_control').addClass('play').html('Play')

  onPlay: =>
    @$('.video_control').removeClass('play').addClass('pause').html('Pause')

  onPause: =>
    @$('.video_control').removeClass('pause').addClass('play').html('Play')

  togglePlayback: (event) =>
    event.preventDefault()
    if $('.video_control').hasClass('play') || $('.video_control').hasClass('pause')
      if @player.isPlaying()
        $(@player).trigger('pause')
      else
        $(@player).trigger('play')
