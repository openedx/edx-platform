# Course Info Section
# This is the implementation of the simplest section
# of the instructor dashboard.

# imports from other modules.
# wrap in (-> ... apply) to defer evaluation
# such that the value can be defined later than this assignment (file load order).
plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments

# A typical section object.
# constructed with $section, a jquery object
# which holds the section body container.
class CourseInfo
  constructor: (@$section) ->
    @$course_errors_wrapper = @$section.find '.course-errors-wrapper'

    # if there are errors
    if @$course_errors_wrapper.length
      @$course_error_toggle = @$course_errors_wrapper.find '.toggle-wrapper'
      @$course_error_toggle_text = @$course_error_toggle.find 'h2'
      @$course_error_visibility_wrapper = @$course_errors_wrapper.find '.course-errors-visibility-wrapper'
      @$course_errors = @$course_errors_wrapper.find '.course-error'

      # append "(34)" to the course errors label
      @$course_error_toggle_text.text @$course_error_toggle_text.text() + " (#{@$course_errors.length})"

      # toggle .open class on errors
      # to show and hide them.
      @$course_error_toggle.click (e) =>
        e.preventDefault()
        if @$course_errors_wrapper.hasClass 'open'
          @$course_errors_wrapper.removeClass 'open'
        else
          @$course_errors_wrapper.addClass 'open'


# export for use
# create parent namespaces if they do not already exist.
# abort if underscore can not be found.
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    CourseInfo: CourseInfo
