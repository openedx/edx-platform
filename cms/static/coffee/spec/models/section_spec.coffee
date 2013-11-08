define ["js/models/section", "sinon"], (Section, sinon) ->
    describe "Section", ->
        describe "basic", ->
            beforeEach ->
                @model = new Section({
                    name: "Life, the Universe, and Everything"
                })

            it "should take a name argument", ->
                expect(@model.get("name")).toEqual("Life, the Universe, and Everything")

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
                    name: "Life, the Universe, and Everything"
                })
                @model.url = 'test_url'
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
