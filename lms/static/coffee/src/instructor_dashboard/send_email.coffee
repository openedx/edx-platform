###
Email Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

# Load utilities
plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments
PendingInstructorTasks = -> window.InstructorDashboard.util.PendingInstructorTasks
create_task_list_table = -> window.InstructorDashboard.util.create_task_list_table.apply this, arguments

class SendEmail
  constructor: (@$container) ->
    # gather elements
    @$emailEditor = XBlock.initializeBlock($('.xblock-studio_view'));
    @$send_to = @$container.find("select[name='send_to']'")
    @$subject = @$container.find("input[name='subject']'")
    @$btn_send = @$container.find("input[name='send']'")
    @$task_response = @$container.find(".request-response")
    @$request_response_error = @$container.find(".request-response-error")
    @$history_request_response_error = @$container.find(".history-request-response-error")
    @$btn_task_history_email = @$container.find("input[name='task-history-email']'")
    @$table_task_history_email = @$container.find(".task-history-email-table")

    # attach click handlers

    @$btn_send.click =>
      if @$subject.val() == ""
        alert gettext("Your message must have a subject.")
      else if @$emailEditor.save()['data'] == ""
        alert gettext("Your message cannot be blank.")
      else
        success_message = gettext("Your email was successfully queued for sending.")
        send_to = @$send_to.val().toLowerCase()
        if send_to == "myself"
          send_to = gettext("yourself")
        else if send_to == "staff"
          send_to = gettext("everyone who is staff or instructor on this course")
        else
          send_to = gettext("ALL (everyone who is enrolled in this course as student, staff, or instructor)")
          success_message = gettext("Your email was successfully queued for sending. Please note that for large classes, it may take up to an hour (or more, if other courses are simultaneously sending email) to send all emails.")
        subject = gettext(@$subject.val())
        confirm_message = gettext("You are about to send an email titled \"#{subject}\" to #{send_to}.  Is this OK?")
        if confirm confirm_message

          send_data =
            action: 'send'
            send_to: @$send_to.val()
            subject: @$subject.val()
            message: @$emailEditor.save()['data']

          $.ajax
            type: 'POST'
            dataType: 'json'
            url: @$btn_send.data 'endpoint'
            data: send_data
            success: (data) =>
              @display_response success_message

            error: std_ajax_err =>
              @fail_with_error gettext('Error sending email.')

        else
          @$task_response.empty()
          @$request_response_error.empty()

    # list task history for email
    @$btn_task_history_email.click =>
      url = @$btn_task_history_email.data 'endpoint'
      $.ajax
        dataType: 'json'
        url: url
        success: (data) =>
          if data.tasks.length
            create_task_list_table @$table_task_history_email, data.tasks
          else
            @$history_request_response_error.text gettext("There is no email history for this course.")
            # Enable the msg-warning css display
            $(".msg-warning").css({"display":"block"})
        error: std_ajax_err =>
          @$history_request_response_error.text gettext("There was an error obtaining email task history for this course.")

  fail_with_error: (msg) ->
    console.warn msg
    @$task_response.empty()
    @$request_response_error.empty()
    @$request_response_error.text gettext(msg)
    $(".msg-confirm").css({"display":"none"})

  display_response: (data_from_server) ->
    @$task_response.empty()
    @$request_response_error.empty()
    @$task_response.text(data_from_server)
    $(".msg-confirm").css({"display":"block"})


# Email Section
class Email
  # enable subsections.
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    # isolate # initialize SendEmail subsection
    plantTimeout 0, => new SendEmail @$section.find '.send-email'

    @instructor_tasks = new (PendingInstructorTasks()) @$section

  # handler for when the section title is clicked.
  onClickTitle: -> @instructor_tasks.task_poller.start()

  # handler for when the section is closed
  onExit: -> @instructor_tasks.task_poller.stop()


# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  Email: Email
