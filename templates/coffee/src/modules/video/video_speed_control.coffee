class VideoSpeedControl
  constructor: (@player, @speeds) ->
    @build()
    @bind()

  $: (selector) ->
    @player.$(selector)

  bind: ->
    $(@player).bind('speedChange', @onSpeedChange)
    @$('.video_speeds a').click @changeVideoSpeed
    if onTouchBasedDevice()
      @$('.speeds').click -> $(this).toggleClass('open')
    else
      @$('.speeds').mouseover -> $(this).addClass('open')
      .mouseout -> $(this).removeClass('open')
      .click (event) ->
        event.preventDefault()
        $(this).removeClass('open')

  build: ->
    $.each @speeds, (index, speed) =>
      link = $('<a>').attr(href: "#").html("#{speed}x")
      @$('.video_speeds').prepend($('<li>').attr('data-speed', speed).html(link))
    @setSpeed(@player.currentSpeed())

  changeVideoSpeed: (event) =>
    event.preventDefault()
    unless $(event.target).parent().hasClass('active')
      $(@player).trigger 'speedChange', $(event.target).parent().data('speed')

  onSpeedChange: (event, speed) =>
    @setSpeed(parseFloat(speed).toFixed(2).replace /\.00$/, '.0')

  setSpeed: (speed) ->
    @$('.video_speeds li').removeClass('active')
    @$(".video_speeds li[data-speed='#{speed}']").addClass('active')
    @$('.speeds p.active').html("#{speed}x")
