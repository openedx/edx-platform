describe "RequireJS", ->
  beforeEach ->
    @addMatchers requirejsTobeUndefined: ->
      typeof requirejs is "undefined"


  it "check that the RequireJS object is present in the global namespace", ->
    expect(RequireJS).toEqual jasmine.any(Object)
    expect(window.RequireJS).toEqual jasmine.any(Object)

  it "check that requirejs(), require(), and define() are not in the global namespace", ->
    expect({}).requirejsTobeUndefined()

    # expect(require).not.toBeDefined();
    # expect(define).not.toBeDefined();
    expect(window.requirejs).not.toBeDefined()
    expect(window.require).not.toBeDefined()
    expect(window.define).not.toBeDefined()
