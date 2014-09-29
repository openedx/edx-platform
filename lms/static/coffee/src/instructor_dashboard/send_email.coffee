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
create_email_content_table = -> window.InstructorDashboard.util.create_email_content_table.apply this, arguments
create_email_message_views = -> window.InstructorDashboard.util.create_email_message_views.apply this, arguments
KeywordValidator = -> window.InstructorDashboard.util.KeywordValidator

class SendEmail
  constructor: (@$container) ->
    # gather elements
    @$emailEditor = XBlock.initializeBlock($('.xblock-studio_view'));
    @$send_to = @$container.find("select[name='send_to']'")
    @$subject = @$container.find("input[name='subject']'")
    @$btn_send = @$container.find("input[name='send']'")
    @$task_response = @$container.find(".request-response")
    @$request_response_error = @$container.find(".request-response-error")
    @$content_request_response_error = @$container.find(".content-request-response-error")
    @$history_request_response_error = @$container.find(".history-request-response-error")
    @$btn_task_history_email = @$container.find("input[name='task-history-email']'")
    @$btn_task_history_email_content = @$container.find("input[name='task-history-email-content']'")
    @$table_task_history_email = @$container.find(".task-history-email-table")
    @$table_email_content_history = @$container.find(".content-history-email-table")
    @$email_content_table_inner = @$container.find(".content-history-table-inner")
    @$email_messages_wrapper = @$container.find(".email-messages-wrapper")

    # attach click handlers

    @$btn_send.click =>
      if @$subject.val() == ""
        alert gettext("Your message must have a subject.")

      else if @$emailEditor.save()['data'] == ""
        alert gettext("Your message cannot be blank.")

      else
        # Validation for keyword substitution
        validation = KeywordValidator().validate_string @$emailEditor.save()['data']
        if not validation.is_valid
          message = gettext("There are invalid keywords in your email. Please check the following keywords and try again:")
          message += "\n" + validation.invalid_keywords.join('\n')
          alert message
          return

        success_message = gettext("Your email was successfully queued for sending.")
        send_to = @$send_to.val().toLowerCase()
        if send_to == "myself"
          confirm_message = gettext("You are about to send an email titled '<%= subject %>' to yourself. Is this OK?")
        else if send_to == "staff"
          confirm_message = gettext("You are about to send an email titled '<%= subject %>' to everyone who is staff or instructor on this course. Is this OK?")
        else
          confirm_message = gettext("You are about to send an email titled '<%= subject %>' to ALL (everyone who is enrolled in this course as student, staff, or instructor). Is this OK?")
          success_message = gettext("Your email was successfully queued for sending. Please note that for large classes, it may take up to an hour (or more, if other courses are simultaneously sending email) to send all emails.")

        subject = @$subject.val()
        full_confirm_message = _.template(confirm_message, {subject: subject})

        if confirm full_confirm_message

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
            @$history_request_response_error.css({"display":"block"})
        error: std_ajax_err =>
          @$history_request_response_error.text gettext("There was an error obtaining email task history for this course.")

    # List content history for emails sent
    @$btn_task_history_email_content.click =>
      url = @$btn_task_history_email_content.data 'endpoint'
      $.ajax
        dataType: 'json'
        url : url
        success: (data) =>
          if data.emails.length
            create_email_content_table @$table_email_content_history, @$email_content_table_inner, data.emails
            create_email_message_views @$email_messages_wrapper, data.emails
          else
            @$content_request_response_error.text gettext("There is no email history for this course.")
            @$content_request_response_error.css({"display":"block"})
        error: std_ajax_err =>
          @$content_request_response_error.text gettext("There was an error obtaining email content history for this course.")

  fail_with_error: (msg) ->
    console.warn msg
    @$task_response.empty()
    @$request_response_error.empty()
    @$request_response_error.text msg
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
