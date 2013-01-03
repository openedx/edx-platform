class @CombinedOpenEnded
  constructor: (element) ->
    @el = $(element).find('section.combined-open-ended')
    @ajax_url = @el.data('ajax-url')
    @reset_button = @$('.reset-button')
    @reset_button.click @reset

  reset: (event) =>
  event.preventDefault()
  if @state == 'done'
    $.postWithPrefix "#{@ajax_url}/reset", {}, (response) =>
      if response.success
        @answer_area.val('')
        @rubric_wrapper.html('')
        @hint_wrapper.html('')
        @message_wrapper.html('')
        @state = 'initial'
        @rebind()
        @reset_button.hide()
      else
        @errors_area.html(response.error)
  else
    @errors_area.html('Problem state got out of sync.  Try reloading the page.')