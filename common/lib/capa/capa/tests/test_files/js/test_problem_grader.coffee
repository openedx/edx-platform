class TestProblemGrader extends XProblemGrader

  constructor: (@submission, @problemState, @parameters={}) ->

    super(@submission, @problemState, @parameters)

  solve: () ->

    @solution = {0: @problemState.value}

  grade: () ->

    if not @solution?
      @solve()

    allCorrect = true

    for id, value of @solution
      valueCorrect = if @submission? then (value == @submission[id]) else false
      @evaluation[id] = valueCorrect
      if not valueCorrect
        allCorrect = false

    return allCorrect

root = exports ? this
root.graderClass = TestProblemGrader
