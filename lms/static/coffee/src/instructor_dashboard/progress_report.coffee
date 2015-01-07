###
Progress Report
###

# A typical section object.
# constructed with $section, a jquery object
# which holds the section body container.
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments
PendingInstructorTasks = -> window.InstructorDashboard.util.PendingInstructorTasks

class ProgressReport 
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    # gather elements
    @$pgreport_generate_btn = @$section.find("input[name='generate-pgreport-csv']'")
    @$pgreport_download_btn = @$section.find("input[name='download-pgreport-csv']'")
    @$pgreport_request_response       = @$section.find '.request-response'
    @$pgreport_request_response_error = @$section.find '.request-response-error'

    @$pgreport_generate_btn.click (e) =>
      @clear_display()
      url = @$pgreport_generate_btn.data 'endpoint'
      $.ajax
        dataType: 'json'
        url: url
        error: std_ajax_err =>
          @clear_display()
          @$pgreport_request_response_error.text gettext("Error generating csv. Please try again.")
          $(".msg-error").css({"display":"block"})
        success: (data) =>
          @clear_display()
          @$pgreport_request_response.text data['status']
          $(".msg-confirm").css({"display":"block"})

    @$pgreport_download_btn.click (e) =>
      url = @$pgreport_download_btn.data 'endpoint'
      location.href = url

  clear_display: ->
    @$pgreport_request_response.empty()
    @$pgreport_request_response_error.empty()
    $(".msg-confirm").css({"display":"none"})
    $(".msg-error").css({"display":"none"})

  onClickTitle: ->
  onExit: ->

# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  ProgressReport: ProgressReport
