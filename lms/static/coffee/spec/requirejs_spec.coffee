describe "RequireJS", ->
  beforeEach ->
    @addMatchers
      requirejsTobeUndefined: ->
        typeof requirejs is "undefined"

      requireTobeUndefined: ->
        typeof require is "undefined"

      defineTobeUndefined: ->
        typeof define is "undefined"


  it "check that the RequireJS object is present in the global namespace", ->
    expect(RequireJS).toEqual jasmine.any(Object)
    expect(window.RequireJS).toEqual jasmine.any(Object)

  it "check that requirejs(), require(), and define() are not in the global namespace", ->
    expect({}).requirejsTobeUndefined()
    expect({}).requireTobeUndefined()
    expect({}).defineTobeUndefined()
    expect(window.requirejs).not.toBeDefined()
    expect(window.require).not.toBeDefined()
    expect(window.define).not.toBeDefined()

  it "check that the RequireJS has requirejs(), require(), and define() functions as its properties", ->
    expect(RequireJS.requirejs).toEqual jasmine.any(Function)
    expect(RequireJS.require).toEqual jasmine.any(Function)
    expect(RequireJS.define).toEqual jasmine.any(Function)
