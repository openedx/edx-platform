# This is a simple class that just hides the error container
# and message container when they are empty
# Can (and should be) expanded upon when our problem list
# becomes more sophisticated
class OpenEnded
  constructor: (ajax_url) ->
    @ajax_url = ajax_url
    @error_container = $('.error-container')
    @error_container.toggle(not @error_container.is(':empty'))

    @message_container = $('.message-container')
    @message_container.toggle(not @message_container.is(':empty'))

    @problem_list = $('.problem-list')

    @ban_button = $('.ban-button')
    @unflag_button = $('.unflag-button')
    @ban_button.click @ban
    @unflag_button.click @unflag

  unflag: (event) =>
    event.preventDefault()

  ban: (event) =>
    event.preventDefault()

  post: (cmd, data, callback) ->
      # if this post request fails, the error callback will catch it
      $.post(@ajax_url + cmd, data, callback)
        .error => callback({success: false, error: "Error occured while performing this operation"})

ajax_url = $('.open-ended-problems').data('ajax_url')
$(document).ready(() -> new OpenEnded(ajax_url))
