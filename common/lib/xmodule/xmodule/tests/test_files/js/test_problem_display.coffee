class MinimaxProblemDisplay extends XProblemDisplay

  constructor: (@state, @submission, @evaluation, @container, @submissionField, @parameters={}) ->

    super(@state, @submission, @evaluation, @container, @submissionField, @parameters)

  render: () ->

  createSubmission: () ->

    @newSubmission = {}

    if @submission?
      for id, value of @submission
        @newSubmission[id] = value

  getCurrentSubmission: () ->
    return @newSubmission

root = exports ? this
root.TestProblemDisplay = TestProblemDisplay
