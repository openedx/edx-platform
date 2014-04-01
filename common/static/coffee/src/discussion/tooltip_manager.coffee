$ ->
  new TooltipManager

class @TooltipManager
  constructor: () ->
    @$body = $('body')
    @$tooltip = $('<div class="tooltip"></div>')
    @$body.delegate '[data-tooltip]',
      'mouseover': @showTooltip,
      'mousemove': @moveTooltip,
      'mouseout': @hideTooltip,
      'click': @hideTooltip

  showTooltip: (e) =>
    $target = $(e.target).closest('[data-tooltip]')
    tooltipText = $target.attr('data-tooltip')
    @$tooltip.html(tooltipText)
    @$body.append(@$tooltip)

    tooltipCoords =
##      x: e.pageX - (@$tooltip.outerWidth() / 2)
##      y: e.pageY - (@$tooltip.outerHeight() + 15)
      x: $(e.target).offset().x
      y: $(e.target).offset().y - 30

    if tooltipCoords.x + @$tooltip.outerWidth() > $(window).width() 
      tooltipCoords.x = $(window).width - @$tooltip.outerWidth()

    @$tooltip.css
    'left': tooltipCoords.x,
    'top': tooltipCoords.y
    'width': "auto"

    @tooltipTimer = setTimeout ()=>

      @$tooltip.show().css('opacity', 1)
      @tooltipTimer = setTimeout ()=>
        @hideTooltip()
      , 3000
    , 500

  moveTooltip: (e) =>
    tooltipCoords =
##      x: e.pageX - (@$tooltip.outerWidth() / 2)
##      y: e.pageY - (@$tooltip.outerHeight() + 15)
      x: $(e.target).offset().left
      y: $(e.target).offset().top - 30

    if tooltipCoords.x + @$tooltip.outerWidth() > $(window).width() 
      tooltipCoords.x = $(window).width - @$tooltip.outerWidth()
    @$tooltip.css
      'left': tooltipCoords.x
      'top': tooltipCoords.y
      'width': "auto"

  hideTooltip: (e) =>
    @$tooltip.hide().css('opacity', 0)
    clearTimeout(@tooltipTimer)
