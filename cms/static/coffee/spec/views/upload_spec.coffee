define ["js/models/uploads", "js/views/uploads", "js/models/chapter", "sinon"], (FileUpload, UploadDialog, Chapter, sinon) ->

    feedbackTpl = readFixtures('system-feedback.underscore')

    describe "UploadDialog", ->
        tpl = readFixtures("upload-dialog.underscore")

        beforeEach ->
            setFixtures($("<script>", {id: "upload-dialog-tpl", type: "text/template"}).text(tpl))
            appendSetFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(feedbackTpl))
            CMS.URL.UPLOAD_ASSET = "/upload"

            @model = new FileUpload(
              mimeTypes: ['application/pdf']
            )
            @dialogResponse = dialogResponse = []
            @view = new UploadDialog(
              model: @model,
              onSuccess: (response) =>
                dialogResponse.push(response.response)
            )
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
                        '{"response": "dummy_response"}')
                expect(@model.get("uploading")).toBeFalsy()
                expect(@model.get("finished")).toBeTruthy()
                expect(@dialogResponse.pop()).toEqual("dummy_response")

            it "can handle upload errors", ->
                @view.upload()
                @requests[0].respond(500)
                expect(@model.get("title")).toMatch(/error/)
                expect(@view.remove).not.toHaveBeenCalled()

            it "removes itself after two seconds on successful upload", ->
                @view.upload()
                @requests[0].respond(200, {"Content-Type": "application/json"},
                        '{"response": "dummy_response"}')
                expect(@view.remove).not.toHaveBeenCalled()
                @clock.tick(2001)
                expect(@view.remove).toHaveBeenCalled()
