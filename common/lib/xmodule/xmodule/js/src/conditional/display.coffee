class @Conditional

  constructor: (element, callerElId) ->
    @el = $(element).find('.conditional-wrapper')

    @callerElId = callerElId

    if callerElId isnt undefined
      dependencies = @el.data('depends')
      if (typeof dependencies is 'string') and (dependencies.length > 0) and (dependencies.indexOf(callerElId) is -1)
        return

    @url = @el.data('url')
    @render(element)

  render: (element) ->
      $.postWithPrefix "#{@url}/conditional_get", (response) =>
        @el.html ''
        @el.append(i) for i in response.html

        parentEl = $(element).parent()
        parentId = parentEl.attr 'id'

        if response.message is false
          if parentEl.hasClass('vert')
            parentEl.hide()
          else
            $(element).hide()
        else
          if parentEl.hasClass('vert')
            parentEl.show()
          else
            $(element).show()

        # The children are rendered with a new request, so they have a different request-token.
        # Use that token instead of @requestToken by simply not passing a token into initializeBlocks.
        XBlock.initializeBlocks(@el)
