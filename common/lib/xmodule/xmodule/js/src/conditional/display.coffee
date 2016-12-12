class @Conditional

  constructor: (element, callerElId) ->
    @el = $(element).find('.conditional-wrapper')

    @callerElId = callerElId

    if callerElId isnt undefined
      dependencies = @el.data('depends')
      if (typeof dependencies is 'string') and (dependencies.length > 0) and (dependencies.indexOf(callerElId) is -1)
        return

    @url = @el.data('url')
    if @url
      @render(element)

  render: (element) ->
    $.postWithPrefix "#{@url}/conditional_get", (response) =>
      parentEl = $(element).parent()
      parentId = parentEl.attr 'id'

      if response.message?
        @el.html ''
        @el.append(i) for i in response.html

        if parentEl.hasClass('vert')
          parentEl.show()
        else
          $(element).show()
      else
        promises = []
        for fragment in response
          promise = XBlock.renderXBlockFragment fragment, @el
          promises.push promise

        $.when.apply(null, promises).always =>
          XBlock.initializeBlocks @el
