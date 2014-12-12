###
Survey Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###


class SurveyDownload
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @
    # gather elements
    @$list_survey_btn = @$section.find("input[name='list-survey']'")

    # attach click handlers
    @$list_survey_btn.click (e) =>
      url = @$list_survey_btn.data 'endpoint'
      location.href = url

  # handler for when the section title is clicked.
  onClickTitle: ->


# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  SurveyDownload: SurveyDownload
