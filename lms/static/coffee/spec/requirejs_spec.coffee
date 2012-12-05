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
  inCallback = undefined
  it "check that we can use RequireJS.define() to create a module", ->
    runs ->
      inCallback = false
      RequireJS.define [], ->
        inCallback = true
        module_status: "OK"


    waitsFor (->
      inCallback
    ), "We should eventually end up in the defined callback", 1000
    runs ->
      expects(inCallback).toBeTruthy()




# it('check that we can use RequireJS.require() to get our defined module', function () {

# });