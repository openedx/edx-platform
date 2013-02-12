class @Conditional

  constructor: (element) ->
    @el = $(element).find('.conditional-wrapper')

    @passed = @el.data('passed') is true
    if @passed is true
      console.log 'Conditional is already passed.'

      return

    console.log 'Conditional is not passed. Must re-check with server.'

    @url = @el.data('url')
    @render()

  render: () ->
      $.postWithPrefix "#{@url}/conditional_get", (response) =>
        console.log response

        if ((response.passed is true) && (@passed is false))
          console.log '(response.passed is true) && (@passed is false)'

          @el.data 'passed', 'true'

          @el.append(i) for i in response.html
          XModule.loadModules @el


