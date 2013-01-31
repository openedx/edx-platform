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
    @gentle_alert "Unflag"

  ban: (event) =>
    event.preventDefault()
    @gentle_alert "Ban"

  post: (cmd, data, callback) ->
      # if this post request fails, the error callback will catch it
      $.post(@ajax_url + cmd, data, callback)
        .error => callback({success: false, error: "Error occured while performing this operation"})

  gentle_alert: (msg) =>
    if $('.message-container').length
      $('.message-container').remove()
    alert_elem = "<div class='message-container'>" + msg + "</div>"
    $('.error-container').after(alert_elem)
    $('.message-container').css(opacity: 0).animate(opacity: 1, 700)

ajax_url = $('.open-ended-problems').data('ajax_url')
$(document).ready(() -> new OpenEnded(ajax_url))
