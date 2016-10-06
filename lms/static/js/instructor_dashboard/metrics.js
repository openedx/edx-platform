# METRICS Section

# imports from other modules.
# wrap in (-> ... apply) to defer evaluation
# such that the value can be defined later than this assignment (file load order).
plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments

#Metrics Section
class Metrics
  constructor: (@$section) ->
    @$section.data 'wrapper', @
    
    
  # handler for when the section title is clicked.
  onClickTitle: ->

# export for use
# create parent namespaces if they do not already exist.
# abort if underscore can not be found.
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    Metrics: Metrics
