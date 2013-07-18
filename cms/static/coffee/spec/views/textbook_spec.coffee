feedbackTpl = readFixtures('system-feedback.underscore')

beforeEach ->
    # remove this when we upgrade jasmine-jquery
    @addMatchers
        toContainText: (text) ->
            trimmedText = $.trim(@actual.text())
            if text and $.isFunction(text.test)
                return text.test(trimmedText)
            else
                return trimmedText.indexOf(text) != -1;

describe "CMS.Views.ShowTextbook", ->
    tpl = readFixtures('show-textbook.underscore')

    beforeEach ->
        setFixtures($("<script>", {id: "show-textbook-tpl", type: "text/template"}).text(tpl))
        appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
        appendSetFixtures(sandbox({id: "page-notification"}))
        appendSetFixtures(sandbox({id: "page-prompt"}))
        @model = new CMS.Models.Textbook({name: "Life Sciences", id: "0life-sciences"})
        spyOn(@model, "destroy").andCallThrough()
        @collection = new CMS.Collections.TextbookSet([@model])
        @view = new CMS.Views.ShowTextbook({model: @model})

        @promptSpies = spyOnConstructor(CMS.Views.Prompt, "Warning", ["show", "hide"])
        @promptSpies.show.andReturn(@promptSpies)
        window.section = new CMS.Models.Section({
            id: "5",
            name: "Course Name",
            url_name: "course_name",
            org: "course_org",
            num: "course_num",
            revision: "course_rev"
        });

    afterEach ->
        delete window.section

    describe "Basic", ->
        it "should render properly", ->
            @view.render()
            expect(@view.$el).toContainText("Life Sciences")

        it "should set the 'editing' property on the model when the edit button is clicked", ->
            @view.render().$(".edit").click()
            expect(@model.get("editing")).toBeTruthy()

        it "should pop a delete confirmation when the delete button is clicked", ->
            @view.render().$(".delete").click()
            expect(@promptSpies.constructor).toHaveBeenCalled()
            ctorOptions = @promptSpies.constructor.mostRecentCall.args[0]
            expect(ctorOptions.title).toMatch(/Life Sciences/)
            # hasn't actually been removed
            expect(@model.destroy).not.toHaveBeenCalled()
            expect(@collection).toContain(@model)

        it "should show chapters appropriately", ->
            @model.get("chapters").add([{}, {}, {}])
            @model.set('showChapters', false)
            @view.render().$(".show-chapters").click()
            expect(@model.get('showChapters')).toBeTruthy()

        it "should hide chapters appropriately", ->
            @model.get("chapters").add([{}, {}, {}])
            @model.set('showChapters', true)
            @view.render().$(".hide-chapters").click()
            expect(@model.get('showChapters')).toBeFalsy()

    describe "AJAX", ->
        beforeEach ->
            @requests = requests = []
            @xhr = sinon.useFakeXMLHttpRequest()
            @xhr.onCreate = (xhr) -> requests.push(xhr)

            @savingSpies = spyOnConstructor(CMS.Views.Notification, "Mini",
                ["show", "hide"])
            @savingSpies.show.andReturn(@savingSpies)

        afterEach ->
            @xhr.restore()

        it "should destroy itself on confirmation", ->
            @view.render().$(".delete").click()
            ctorOptions = @promptSpies.constructor.mostRecentCall.args[0]
            # run the primary function to indicate confirmation
            ctorOptions.actions.primary.click(@promptSpies)
            # AJAX request has been sent, but not yet returned
            expect(@model.destroy).toHaveBeenCalled()
            expect(@requests.length).toEqual(1)
            expect(@savingSpies.constructor).toHaveBeenCalled()
            expect(@savingSpies.show).toHaveBeenCalled()
            expect(@savingSpies.hide).not.toHaveBeenCalled()
            savingOptions = @savingSpies.constructor.mostRecentCall.args[0]
            expect(savingOptions.title).toMatch(/Deleting/)
            # return a success response
            @requests[0].respond(200)
            expect(@savingSpies.hide).toHaveBeenCalled()
            expect(@collection.contains(@model)).toBeFalsy()

describe "CMS.Views.EditTextbook", ->
    describe "Basic", ->
        tpl = readFixtures('edit-textbook.underscore')
        chapterTpl = readFixtures('edit-chapter.underscore')

        beforeEach ->
            setFixtures($("<script>", {id: "edit-textbook-tpl", type: "text/template"}).text(tpl))
            appendSetFixtures($("<script>", {id: "edit-chapter-tpl", type: "text/template"}).text(chapterTpl))
            appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
            appendSetFixtures(sandbox({id: "page-notification"}))
            appendSetFixtures(sandbox({id: "page-prompt"}))
            @model = new CMS.Models.Textbook({name: "Life Sciences", editing: true})
            spyOn(@model, 'save')
            @collection = new CMS.Collections.TextbookSet()
            @collection.add(@model)
            @view = new CMS.Views.EditTextbook({model: @model})
            spyOn(@view, 'render').andCallThrough()

        it "should render properly", ->
            @view.render()
            expect(@view.$("input[name=textbook-name]").val()).toEqual("Life Sciences")

        it "should allow you to create new empty chapters", ->
            @view.render()
            numChapters = @model.get("chapters").length
            @view.$(".action-add-chapter").click()
            expect(@model.get("chapters").length).toEqual(numChapters+1)
            expect(@model.get("chapters").last().isEmpty()).toBeTruthy()

        it "should save properly", ->
            @view.render()
            @view.$("input[name=textbook-name]").val("starfish")
            @view.$("input[name=chapter1-name]").val("wallflower")
            @view.$("input[name=chapter1-asset-path]").val("foobar")
            @view.$("form").submit()
            expect(@model.get("name")).toEqual("starfish")
            chapter = @model.get("chapters").first()
            expect(chapter.get("name")).toEqual("wallflower")
            expect(chapter.get("asset_path")).toEqual("foobar")
            expect(@model.save).toHaveBeenCalled()

        it "should not save on invalid", ->
            @view.render()
            @view.$("input[name=textbook-name]").val("")
            @view.$("input[name=chapter1-asset-path]").val("foobar.pdf")
            @view.$("form").submit()
            expect(@model.validationError).toBeTruthy()
            expect(@model.save).not.toHaveBeenCalled()

        it "does not save on cancel", ->
            @model.get("chapters").add([{name: "a", asset_path: "b"}])
            @view.render()
            @view.$("input[name=textbook-name]").val("starfish")
            @view.$("input[name=chapter1-asset-path]").val("foobar.pdf")
            @view.$(".action-cancel").click()
            expect(@model.get("name")).not.toEqual("starfish")
            chapter = @model.get("chapters").first()
            expect(chapter.get("asset_path")).not.toEqual("foobar")
            expect(@model.save).not.toHaveBeenCalled()

        it "should be possible to correct validation errors", ->
            @view.render()
            @view.$("input[name=textbook-name]").val("")
            @view.$("input[name=chapter1-asset-path]").val("foobar.pdf")
            @view.$("form").submit()
            expect(@model.validationError).toBeTruthy()
            expect(@model.save).not.toHaveBeenCalled()
            @view.$("input[name=textbook-name]").val("starfish")
            @view.$("input[name=chapter1-name]").val("foobar")
            @view.$("form").submit()
            expect(@model.validationError).toBeFalsy()
            expect(@model.save).toHaveBeenCalled()

        it "removes all empty chapters on cancel if the model has a non-empty chapter", ->
            chapters = @model.get("chapters")
            chapters.at(0).set("name", "non-empty")
            @model.setOriginalAttributes()
            @view.render()
            chapters.add([{}, {}, {}]) # add three empty chapters
            expect(chapters.length).toEqual(4)
            @view.$(".action-cancel").click()
            expect(chapters.length).toEqual(1)
            expect(chapters.first().get('name')).toEqual("non-empty")

        it "removes all empty chapters on cancel except one if the model has no non-empty chapters", ->
            chapters = @model.get("chapters")
            @view.render()
            chapters.add([{}, {}, {}]) # add three empty chapters
            expect(chapters.length).toEqual(4)
            @view.$(".action-cancel").click()
            expect(chapters.length).toEqual(1)


describe "CMS.Views.ListTextbooks", ->
    noTextbooksTpl = readFixtures("no-textbooks.underscore")

    beforeEach ->
        setFixtures($("<script>", {id: "no-textbooks-tpl", type: "text/template"}).text(noTextbooksTpl))
        appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
        @showSpies = spyOnConstructor(CMS.Views, "ShowTextbook", ["render"])
        @showSpies.render.andReturn(@showSpies) # equivalent of `return this`
        showEl = $("<li>")
        @showSpies.$el = showEl
        @showSpies.el = showEl.get(0)
        @editSpies = spyOnConstructor(CMS.Views, "EditTextbook", ["render"])
        editEl = $("<li>")
        @editSpies.render.andReturn(@editSpies)
        @editSpies.$el = editEl
        @editSpies.el= editEl.get(0)

        @collection = new CMS.Collections.TextbookSet
        @view = new CMS.Views.ListTextbooks({collection: @collection})
        @view.render()

    it "should render the empty template if there are no textbooks", ->
        expect(@view.$el).toContainText("You haven't added any textbooks to this course yet")
        expect(@view.$el).toContain(".new-button")
        expect(@showSpies.constructor).not.toHaveBeenCalled()
        expect(@editSpies.constructor).not.toHaveBeenCalled()

    it "should render ShowTextbook views by default if no textbook is being edited", ->
        # add three empty textbooks to the collection
        @collection.add([{}, {}, {}])
        # reset spies due to re-rendering on collection modification
        @showSpies.constructor.reset()
        @editSpies.constructor.reset()
        # render once and test
        @view.render()

        expect(@view.$el).not.toContainText(
            "You haven't added any textbooks to this course yet")
        expect(@showSpies.constructor).toHaveBeenCalled()
        expect(@showSpies.constructor.calls.length).toEqual(3);
        expect(@editSpies.constructor).not.toHaveBeenCalled()

    it "should render an EditTextbook view for a textbook being edited", ->
        # add three empty textbooks to the collection: the first and third
        # should be shown, and the second should be edited
        @collection.add([{editing: false}, {editing: true}, {editing: false}])
        editing = @collection.at(1)
        expect(editing.get("editing")).toBeTruthy()
        # reset spies
        @showSpies.constructor.reset()
        @editSpies.constructor.reset()
        # render once and test
        @view.render()

        expect(@showSpies.constructor).toHaveBeenCalled()
        expect(@showSpies.constructor.calls.length).toEqual(2)
        expect(@showSpies.constructor).not.toHaveBeenCalledWith({model: editing})
        expect(@editSpies.constructor).toHaveBeenCalled()
        expect(@editSpies.constructor.calls.length).toEqual(1)
        expect(@editSpies.constructor).toHaveBeenCalledWith({model: editing})

    it "should add a new textbook when the new-button is clicked", ->
        # reset spies
        @showSpies.constructor.reset()
        @editSpies.constructor.reset()
        # test
        @view.$(".new-button").click()

        expect(@collection.length).toEqual(1)
        expect(@view.$el).toContain(@editSpies.$el)
        expect(@view.$el).not.toContain(@showSpies.$el)


describe "CMS.Views.EditChapter", ->
    tpl = readFixtures("edit-chapter.underscore")

    beforeEach ->
        setFixtures($("<script>", {id: "edit-chapter-tpl", type: "text/template"}).text(tpl))
        appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
        @model = new CMS.Models.Chapter
            name: "Chapter 1"
            asset_path: "/ch1.pdf"
        @collection = new CMS.Collections.ChapterSet()
        @collection.add(@model)
        @view = new CMS.Views.EditChapter({model: @model})
        spyOn(@view, "remove").andCallThrough()
        CMS.URL.UPLOAD_ASSET = "/upload"
        window.section = new CMS.Models.Section({name: "abcde"})

    afterEach ->
        delete CMS.URL.UPLOAD_ASSET
        delete window.section

    it "can render", ->
        @view.render()
        expect(@view.$("input.chapter-name").val()).toEqual("Chapter 1")
        expect(@view.$("input.chapter-asset-path").val()).toEqual("/ch1.pdf")

    it "can delete itself", ->
        @view.render().$(".action-close").click()
        expect(@collection.length).toEqual(0)
        expect(@view.remove).toHaveBeenCalled()

    it "can open an upload dialog", ->
        uploadSpies = spyOnConstructor(CMS.Views, "UploadDialog", ["show", "el"])
        uploadSpies.show.andReturn(uploadSpies)

        @view.render().$(".action-upload").click()
        ctorOptions = uploadSpies.constructor.mostRecentCall.args[0]
        expect(ctorOptions.model.get('title')).toMatch(/abcde/)
        expect(ctorOptions.chapter).toBe(@model)
        expect(uploadSpies.show).toHaveBeenCalled()

    it "saves content when opening upload dialog", ->
        @view.render()
        @view.$("input.chapter-name").val("rainbows")
        @view.$("input.chapter-asset-path").val("unicorns")
        @view.$(".action-upload").click()
        expect(@model.get("name")).toEqual("rainbows")
        expect(@model.get("asset_path")).toEqual("unicorns")


describe "CMS.Views.UploadDialog", ->
    tpl = readFixtures("upload-dialog.underscore")

    beforeEach ->
        setFixtures($("<script>", {id: "upload-dialog-tpl", type: "text/template"}).text(tpl))
        appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
        CMS.URL.UPLOAD_ASSET = "/upload"

        @model = new CMS.Models.FileUpload()
        @chapter = new CMS.Models.Chapter()
        @view = new CMS.Views.UploadDialog({model: @model, chapter: @chapter})
        spyOn(@view, 'remove').andCallThrough()

        # create mock file input, so that we aren't subject to browser restrictions
        @mockFiles = []
        mockFileInput = jasmine.createSpy('mockFileInput')
        mockFileInput.files = @mockFiles
        jqMockFileInput = jasmine.createSpyObj('jqMockFileInput', ['get', 'replaceWith'])
        jqMockFileInput.get.andReturn(mockFileInput)
        realMethod = @view.$
        spyOn(@view, "$").andCallFake (selector) ->
            if selector == "input[type=file]"
                jqMockFileInput
            else
                realMethod.apply(this, arguments)

    afterEach ->
        delete CMS.URL.UPLOAD_ASSET

    describe "Basic", ->
        it "should be shown by default", ->
            expect(@view.options.shown).toBeTruthy()

        it "should render without a file selected", ->
            @view.render()
            expect(@view.$el).toContain("input[type=file]")
            expect(@view.$(".action-upload")).toHaveClass("disabled")

        it "should render with a PDF selected", ->
            file = {name: "fake.pdf", "type": "application/pdf"}
            @mockFiles.push(file)
            @model.set("selectedFile", file)
            @view.render()
            expect(@view.$el).toContain("input[type=file]")
            expect(@view.$el).not.toContain("#upload_error")
            expect(@view.$(".action-upload")).not.toHaveClass("disabled")

        it "should render an error with an invalid file type selected", ->
            file = {name: "fake.png", "type": "image/png"}
            @mockFiles.push(file)
            @model.set("selectedFile", file)
            @view.render()
            expect(@view.$el).toContain("input[type=file]")
            expect(@view.$el).toContain("#upload_error")
            expect(@view.$(".action-upload")).toHaveClass("disabled")


        it "adds body class on show()", ->
            @view.show()
            expect(@view.options.shown).toBeTruthy()
            # can't test: this blows up the spec runner
            # expect($("body")).toHaveClass("dialog-is-shown")

        it "removes body class on hide()", ->
            @view.hide()
            expect(@view.options.shown).toBeFalsy()
            # can't test: this blows up the spec runner
            # expect($("body")).not.toHaveClass("dialog-is-shown")

    describe "Uploads", ->
        beforeEach ->
            @requests = requests = []
            @xhr = sinon.useFakeXMLHttpRequest()
            @xhr.onCreate = (xhr) -> requests.push(xhr)
            @clock = sinon.useFakeTimers()

        afterEach ->
            @xhr.restore()
            @clock.restore()

        it "can upload correctly", ->
            @view.upload()
            expect(@model.get("uploading")).toBeTruthy()
            expect(@requests.length).toEqual(1)
            request = @requests[0]
            expect(request.url).toEqual("/upload")
            expect(request.method).toEqual("POST")

            request.respond(200, {"Content-Type": "application/json"},
                    '{"displayname": "starfish", "url": "/uploaded/starfish.pdf"}')
            expect(@model.get("uploading")).toBeFalsy()
            expect(@model.get("finished")).toBeTruthy()
            expect(@chapter.get("name")).toEqual("starfish")
            expect(@chapter.get("asset_path")).toEqual("/uploaded/starfish.pdf")

        it "can handle upload errors", ->
            @view.upload()
            @requests[0].respond(500)
            expect(@model.get("title")).toMatch(/error/)
            expect(@view.remove).not.toHaveBeenCalled()

        it "removes itself after two seconds on successful upload", ->
            @view.upload()
            @requests[0].respond(200, {"Content-Type": "application/json"},
                    '{"displayname": "starfish", "url": "/uploaded/starfish.pdf"}')
            expect(@view.remove).not.toHaveBeenCalled()
            @clock.tick(2001)
            expect(@view.remove).toHaveBeenCalled()
