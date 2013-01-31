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
    parent_tr = $(event.target).parent().parent()
    tr_children = parent_tr.children()
    action_type = "unflag"
    submission_id = tr_children[4].innerText
    student_id = tr_children[5].innerText
    @post('take_action_on_flags', {'submission_id' : submission_id, 'student_id' : student_id, 'action_type' : action_type}, @handle_after_action)

  ban: (event) =>
    event.preventDefault()
    parent_tr = $(event.target).parent().parent()
    tr_children = parent_tr.children()
    action_type = "ban"
    submission_id = tr_children[4].innerText
    student_id = tr_children[5].innerText
    @post('take_action_on_flags', {'submission_id' : submission_id, 'student_id' : student_id, 'action_type' : action_type}, @handle_after_action)

  post: (cmd, data, callback) ->
      # if this post request fails, the error callback will catch it
      $.post(@ajax_url + cmd, data, callback)
        .error => callback({success: false, error: "Error occured while performing this operation"})

  handle_after_action: (data) ->
    @gentle_alert data.data

  gentle_alert: (msg) =>
    if $('.message-container').length
      $('.message-container').remove()
    alert_elem = "<div class='message-container'>" + msg + "</div>"
    $('.error-container').after(alert_elem)
    $('.message-container').css(opacity: 0).animate(opacity: 1, 700)

ajax_url = $('.open-ended-problems').data('ajax_url')
$(document).ready(() -> new OpenEnded(ajax_url))
