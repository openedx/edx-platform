class TestProblemGenerator extends XProblemGenerator

  constructor: (seed, @parameters = {}) ->

    super(seed, @parameters)

  generate: () ->

    @problemState.value = @parameters.value

    return @problemState

root = exports ? this
root.generatorClass = TestProblemGenerator
