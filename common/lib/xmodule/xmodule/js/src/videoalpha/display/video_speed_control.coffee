class @VideoSpeedControlAlpha extends SubviewAlpha
  bind: ->
    @$('.video_speeds a').click @changeVideoSpeed
    if onTouchBasedDevice()
      @$('.speeds').click (event) ->
        event.preventDefault()
        $(this).toggleClass('open')
    else
      @$('.speeds').mouseenter ->
        $(this).addClass('open')
      @$('.speeds').mouseleave ->
        $(this).removeClass('open')
      @$('.speeds').click (event) ->
        event.preventDefault()
        $(this).removeClass('open')

  render: ->
    @el.prepend """
      <div class="speeds">
        <a href="#">
          <h3>Speed</h3>
          <p class="active"></p>
        </a>
        <ol class="video_speeds"></ol>
      </div>
      """
    $.each @speeds, (index, speed) =>
      link = $('<a>').attr(href: "#").html("#{speed}x")
      @$('.video_speeds').prepend($('<li>').attr('data-speed', speed).html(link))
    @setSpeed @currentSpeed

  reRender: (newSpeeds, currentSpeed) ->
    @$('.video_speeds').empty()
    @$('.video_speeds li').removeClass('active')
    @speeds = newSpeeds
    $.each @speeds, (index, speed) =>
      link = $('<a>').attr(href: "#").html("#{speed}x")
      listItem = $('<li>').attr('data-speed', speed).html(link);
      listItem.addClass('active') if speed is currentSpeed
      @$('.video_speeds').prepend listItem
    @$('.video_speeds a').click @changeVideoSpeed

  changeVideoSpeed: (event) =>
    event.preventDefault()
    unless $(event.target).parent().hasClass('active')
      @currentSpeed = $(event.target).parent().data('speed')
      $(@).trigger 'speedChange', $(event.target).parent().data('speed')
      @setSpeed(parseFloat(@currentSpeed).toFixed(2).replace /\.00$/, '.0')

  setSpeed: (speed) ->
    @$('.video_speeds li').removeClass('active')
    @$(".video_speeds li[data-speed='#{speed}']").addClass('active')
    @$('.speeds p.active').html("#{speed}x")
