log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms

class CourseInfo
  constructor: (@$section) ->
    log "setting up instructor dashboard section - course info"
    @$section.data 'wrapper', @

    @$course_errors_wrapper = @$section.find '.course-errors-wrapper'

    if @$course_errors_wrapper.length
      @$course_error_toggle = @$course_errors_wrapper.find('h2').eq(0)
      @$course_error_visibility_wrapper = @$course_errors_wrapper.find '.course-errors-visibility-wrapper'
      @$course_errors = @$course_errors_wrapper.find('.course-error')

      @$course_error_toggle.text @$course_error_toggle.text() + " (#{@$course_errors.length})"

      @$course_error_toggle.click (e) =>
        e.preventDefault()
        @$course_error_visibility_wrapper.toggle()


# exports
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    CourseInfo: CourseInfo
