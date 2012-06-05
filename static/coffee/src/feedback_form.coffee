class @FeedbackForm
  constructor: ->
    $('#feedback_button').click ->
      data =
        subject: $('#feedback_subject').val()
        message: $('#feedback_message').val()
        url: window.location.href
      $.postWithPrefix '/send_feedback', data, ->
        $('#feedback_div').html 'Feedback submitted. Thank you'
      ,'json'
