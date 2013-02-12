class @Conditional

  constructor: (element) ->
    @el = $(element).find('.conditional-wrapper')

    if @el.data('passed') is true
      @passed = true

      return
    else if @el.data('passed') is false
      @passed = false
    else
      @passed = null

    @url = @el.data('url')
    @render()

  render: () ->
      $.postWithPrefix "#{@url}/conditional_get", (response) =>
        if (((response.passed is true) && (@passed is false)) || (@passed is null))
          @el.data 'passed', response.passed

          @el.html ''
          @el.append(i) for i in response.html
          XModule.loadModules @el
