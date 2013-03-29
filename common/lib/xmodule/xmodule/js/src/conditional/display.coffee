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
          if parentId.indexOf('vert') is 0
            parentEl.hide()
          else
            $(element).hide()
        else
          if parentId.indexOf('vert') is 0
            parentEl.show()
          else
            $(element).show()

        XModule.loadModules @el
