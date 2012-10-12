class XProblemGenerator
  
  constructor: (seed, @parameters={}) ->

    @random = new MersenneTwister(seed)

    @problemState = {}

  generate: () ->

    console.error("Abstract method called: XProblemGenerator.generate")

class XProblemDisplay

  constructor: (@state, @submission, @evaluation, @container, @submissionField, @parameters={}) ->

  render: () ->

    console.error("Abstract method called: XProblemDisplay.render")

  updateSubmission: () ->

    @submissionField.val(JSON.stringify(@getCurrentSubmission()))

  getCurrentSubmission: () ->
    console.error("Abstract method called: XProblemDisplay.getCurrentSubmission")

class XProblemGrader

  constructor: (@submission, @problemState, @parameters={}) ->

    @solution   = null
    @evaluation = {}

  solve: () ->

    console.error("Abstract method called: XProblemGrader.solve")

  grade: () ->

    console.error("Abstract method called: XProblemGrader.grade")

root = exports ? this

root.XProblemGenerator = XProblemGenerator
root.XProblemDisplay   = XProblemDisplay
root.XProblemGrader    = XProblemGrader
