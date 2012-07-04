class @VideoControl extends Subview
  bind: ->
    @$('.video_control').click @togglePlayback

  render: ->
    @el.append """
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

  play: ->
    @$('.video_control').removeClass('play').addClass('pause').html('Pause')

  pause: ->
    @$('.video_control').removeClass('pause').addClass('play').html('Play')

  togglePlayback: (event) =>
    event.preventDefault()
    if @$('.video_control').hasClass('play')
      $(@).trigger('play')
    else if @$('.video_control').hasClass('pause')
      $(@).trigger('pause')
