class @ImageExplorer
  # The client side code for ImageExplorer xModule

  constructor: (element) ->
    @el = $(element).find('.image-explorer-xmodule-wrapper')
    @bind()

  $: (selector) ->
    $(selector, @el)

  bind: =>
    @$('.image-explorer-hotspot').click @hotspot_clicked
    @$('.image-explorer-close-reveal').click @hotspot_closed_clicked
    @el.click @close_hotspots

  close_hotspots: =>
    @$('.image-explorer-hotspot-reveal').css('display', 'none')
    return

  hotspot_clicked: (eventObj) =>
    eventObj.preventDefault()
    eventObj.stopPropagation()

    @close_hotspots()
    target = @$(eventObj.currentTarget)
    target_position_left = target.position().left
    hotspot_image_width = target.outerWidth()

    reveal = target.find('.image-explorer-hotspot-reveal')

    # see the width of the hotspot to show, see if it goes too far to the right
    # if so then have the reveal go to the left of the hotspot icon
    reveal_width = reveal.outerWidth()
    parent_wrapper = reveal.parents('.image-explorer-hotspot')
    image_element = parent_wrapper.siblings('.image-explorer-background')
    image_width = image_element.outerWidth()

    if (target_position_left + reveal_width > image_width) and (target_position_left - reveal_width - hotspot_image_width > 0)
      reveal.css('margin-left', '-' + (reveal_width + hotspot_image_width) + 'px')

    # show the reveal
    reveal.css('display', 'block')
    return

  hotspot_closed_clicked: (eventObj) =>
    eventObj.preventDefault()
    eventObj.stopPropagation()
    @close_hotspots()
    return
