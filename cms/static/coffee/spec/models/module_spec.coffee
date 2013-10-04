define ["coffee/src/models/module"], (Module) ->
    describe "Module", ->
        it "set the correct URL", ->
            expect(new Module().url).toEqual("/save_item")

        it "set the correct default", ->
            expect(new Module().defaults).toEqual(undefined)
