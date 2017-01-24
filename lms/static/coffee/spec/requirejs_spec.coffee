describe "RequireJS namespacing", ->
    beforeEach ->

        # Jasmine does not provide a way to use the typeof operator. We need
        # to create our own custom matchers so that a TypeError is not thrown.
        jasmine.addMatchers
            requirejsTobeUndefined: ->
                {
                compare: ->
                    {
                        pass: typeof requirejs is "undefined"
                    }
                }

            requireTobeUndefined: ->
                {
                compare: ->
                    {
                        pass: typeof require is "undefined"
                    }
                }

            defineTobeUndefined: ->
                {
                compare: ->
                    {
                        pass: typeof define is "undefined"
                    }
                }


    it "check that the RequireJS object is present in the global namespace", ->
        expect(RequireJS).toEqual jasmine.any(Object)
        expect(window.RequireJS).toEqual jasmine.any(Object)

    it "check that requirejs(), require(), and define() are not in the global namespace", ->

        # The custom matchers that we defined in the beforeEach() function do
        # not operate on an object. We pass a dummy empty object {} not to
        # confuse Jasmine.
        expect({}).requirejsTobeUndefined()
        expect({}).requireTobeUndefined()
        expect({}).defineTobeUndefined()
        expect(window.requirejs).not.toBeDefined()
        expect(window.require).not.toBeDefined()
        expect(window.define).not.toBeDefined()


describe "RequireJS module creation", ->
    inDefineCallback = undefined
    inRequireCallback = undefined
    it "check that we can use RequireJS to define() and require() a module", (done) ->
        d1 = $.Deferred()
        d2 = $.Deferred()
        # Because Require JS works asynchronously when defining and requiring
        # modules, we need to use the special Jasmine functions runs(), and
        # waitsFor() to set up this test.
        func = () ->

            # Initialize the variable that we will test for. They will be set
            # to true in the appropriate callback functions called by Require
            # JS. If their values do not change, this will mean that something
            # is not working as is intended.
            inDefineCallback = false
            inRequireCallback = false

            # Define our test module.
            RequireJS.define "test_module", [], ->
                inDefineCallback = true

                d1.resolve()

                # This module returns an object. It can be accessed via the
                # Require JS require() function.
                module_status: "OK"


            # Require our defined test module.
            RequireJS.require ["test_module"], (test_module) ->
                inRequireCallback = true

                # If our test module was defined properly, then we should
                # be able to get the object it returned, and query some
                # property.
                expect(test_module.module_status).toBe "OK"

                d2.resolve()

        func()
        # We will wait before checking if our module was defined and that we were able to require() the module.
        $.when(d1, d2).done(->
            # The final test behavior
            expect(inDefineCallback).toBeTruthy()
            expect(inRequireCallback).toBeTruthy()
        ).always(done)
