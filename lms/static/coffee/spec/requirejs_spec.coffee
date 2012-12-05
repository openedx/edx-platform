describe "RequireJS namespacing", ->
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


describe "RequireJS module creation", ->
  inDefineCallback = undefined
  inRequireCallback = undefined
  it "check that we can use RequireJS define() and require() a module", ->
    runs ->
      inDefineCallback = false
      inRequireCallback = false
      RequireJS.define "test_module", [], ->
        inDefineCallback = true
        module_status: "OK"

      RequireJS.require ["test_module"], (test_module) ->
        inRequireCallback = true
        expects(test_module.module_status).toBe "OK"


    waitsFor (->
      return false  if (inDefineCallback isnt true) or (inRequireCallback isnt true)
      true
    ), "We should eventually end up in the defined callback", 1000
    runs ->
      expects(inDefineCallback).toBeTruthy()
      expects(inRequireCallback).toBeTruthy()


