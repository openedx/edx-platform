define ["js/models/section", "js/spec_helpers/create_sinon", "js/utils/module"], (Section, create_sinon, ModuleUtils) ->
    describe "Section", ->
        describe "basic", ->
            beforeEach ->
                @model = new Section({
                    id: 42
                    name: "Life, the Universe, and Everything"
                })

            it "should take an id argument", ->
                expect(@model.get("id")).toEqual(42)

            it "should take a name argument", ->
                expect(@model.get("name")).toEqual("Life, the Universe, and Everything")

            it "should have a URL set", ->
                expect(@model.url()).toEqual(ModuleUtils.getUpdateUrl(42))

            it "should serialize to JSON correctly", ->
                expect(@model.toJSON()).toEqual({
                metadata:
                    {
                    display_name: "Life, the Universe, and Everything"
                    }
                })

        describe "XHR", ->
            beforeEach ->
                spyOn(Section.prototype, 'showNotification')
                spyOn(Section.prototype, 'hideNotification')
                @model = new Section({
                    id: 42
                    name: "Life, the Universe, and Everything"
                })

            it "show/hide a notification when it saves to the server", ->
                server = create_sinon['server'](200, this)

                @model.save()
                expect(Section.prototype.showNotification).toHaveBeenCalled()
                server.respond()
                expect(Section.prototype.hideNotification).toHaveBeenCalled()

            it "don't hide notification when saving fails", ->
                # this is handled by the global AJAX error handler
                server = create_sinon['server'](500, this)

                @model.save()
                server.respond()
                expect(Section.prototype.hideNotification).not.toHaveBeenCalled()
