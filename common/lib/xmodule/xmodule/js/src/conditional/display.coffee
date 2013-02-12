class @Conditional

  constructor: (element) ->
    @el = $(element).find('.conditional-wrapper')

    if @el.data('passed') is true
      @passed = true

      console.log 'Conditional is already passed.'

      return
    else if @el.data('passed') is false
      @passed = false
    else
      @passed = null

    console.log '@passed = '
    console.log @passed

    console.log 'Conditional is not passed. Must re-check with server.'

    @url = @el.data('url')
    @render()

  render: () ->
      $.postWithPrefix "#{@url}/conditional_get", (response) =>
        console.log response

        if (((response.passed is true) && (@passed is false)) || (@passed is null))
          console.log '(((response.passed is true) && (@passed is false)) || (@passed is null))'

          @el.data 'passed', true

          @el.append(i) for i in response.html
          XModule.loadModules @el
