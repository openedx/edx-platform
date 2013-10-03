# Email Section

# imports from other modules.
# wrap in (-> ... apply) to defer evaluation
# such that the value can be defined later than this assignment (file load order).
plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments

class SendEmail
  constructor: (@$container) ->
    # gather elements
    @$emailEditor = XModule.loadModule($('.xmodule_edit'));
    @$send_to = @$container.find("select[name='send_to']'")
    @$subject = @$container.find("input[name='subject']'")
    #message = emailEditor.save()['data']
    @$btn_send = @$container.find("input[name='send']'")
    @$task_response = @$container.find(".request-response")
    @$request_response_error = @$container.find(".request-response-error")

    # attach click handlers

    @$btn_send.click =>
      
      send_data =
        action: 'send'
        send_to: @$send_to.val()
        subject: @$subject.val()
        message: @$emailEditor.save()['data']
        #message: @$message.val()

      $.ajax
        dataType: 'json'
        url: @$btn_send.data 'endpoint'
        data: send_data
        success: (data) => @display_response "Your email was successfully queued for sending."
        error: std_ajax_err => @fail_with_error "Error sending email."

  fail_with_error: (msg) ->
    console.warn msg
    @$task_response.empty()
    @$request_response_error.empty()
    @$request_response_error.text msg

  display_response: (data_from_server) ->
    @$task_response.empty()
    @$request_response_error.empty()
    @$task_response.text("Your email was successfully queued for sending.")


# Email Section
class Email
  # enable subsections.
  constructor: (@$section) ->
    # attach self to html
    # so that instructor_dashboard.coffee can find this object
    # to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    # isolate # initialize SendEmail subsection
    plantTimeout 0, => new SendEmail @$section.find '.send-email'

  # handler for when the section title is clicked.
  onClickTitle: ->


# export for use
# create parent namespaces if they do not already exist.
# abort if underscore can not be found.
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    Email: Email
