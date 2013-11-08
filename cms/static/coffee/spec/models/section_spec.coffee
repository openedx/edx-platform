define ["js/models/section", "sinon"], (Section, sinon) ->
    describe "Section", ->
        describe "basic", ->
            beforeEach ->
                @model = new Section({
                    id: 42,
                    name: "Life, the Universe, and Everything"
                })

            it "should take an id argument", ->
                expect(@model.get("id")).toEqual(42)

            it "should take a name argument", ->
                expect(@model.get("name")).toEqual("Life, the Universe, and Everything")

            it "should have a URL set", ->
                expect(@model.url).toEqual("/save_item")

            it "should serialize to JSON correctly", ->
                expect(@model.toJSON()).toEqual({
                id: 42,
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
                    id: 42,
                    name: "Life, the Universe, and Everything"
                })
                @requests = requests = []
                @xhr = sinon.useFakeXMLHttpRequest()
                @xhr.onCreate = (xhr) -> requests.push(xhr)

            afterEach ->
                @xhr.restore()

            it "show/hide a notification when it saves to the server", ->
                @model.save()
                expect(Section.prototype.showNotification).toHaveBeenCalled()
                @requests[0].respond(200)
                expect(Section.prototype.hideNotification).toHaveBeenCalled()

            it "don't hide notification when saving fails", ->
                # this is handled by the global AJAX error handler
                @model.save()
                @requests[0].respond(500)
                expect(Section.prototype.hideNotification).not.toHaveBeenCalled()
