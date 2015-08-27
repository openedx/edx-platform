define ["js/models/uploads", "js/views/uploads", "js/models/chapter", "common/js/spec_helpers/ajax_helpers", "js/spec_helpers/modal_helpers"], (FileUpload, UploadDialog, Chapter, AjaxHelpers, modal_helpers) ->

    describe "UploadDialog", ->
        tpl = readFixtures("upload-dialog.underscore")

        beforeEach ->
            modal_helpers.installModalTemplates()
            appendSetFixtures($("<script>", {id: "upload-dialog-tpl", type: "text/template"}).text(tpl))
            CMS.URL.UPLOAD_ASSET = "/upload"

            @model = new FileUpload(
              mimeTypes: ['application/pdf']
            )
            @dialogResponse = dialogResponse = []
            @view = new UploadDialog(
              model: @model,
              url:  CMS.URL.UPLOAD_ASSET,
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
            if (@view && modal_helpers.isShowingModal(@view))
                @view.hide()

        describe "Basic", ->
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

            it "should render an error with an invalid file type after a correct file type selected", ->
                correctFile = {name: "fake.pdf", "type": "application/pdf"}
                inCorrectFile = {name: "fake.png", "type": "image/png"}
                event = {}
                @view.render()

                event.target = {"files": [correctFile]}
                @view.selectFile(event)
                expect(@view.$el).toContain("input[type=file]")
                expect(@view.$el).not.toContain("#upload_error")
                expect(@view.$(".action-upload")).not.toHaveClass("disabled")

                realMethod = @model.set
                spyOn(@model, "set").andCallFake (data) ->
                  if data.selectedFile != undefined
                    this.attributes.selectedFile = data.selectedFile
                    this.changed = {}
                  else
                    realMethod.apply(this, arguments)

                event.target = {"files": [inCorrectFile]}
                @view.selectFile(event)
                expect(@view.$el).toContain("input[type=file]")
                expect(@view.$el).toContain("#upload_error")
                expect(@view.$(".action-upload")).toHaveClass("disabled")

        describe "Uploads", ->
            beforeEach ->
                @clock = sinon.useFakeTimers()

            afterEach ->
                @clock.restore()

            it "can upload correctly", ->
                requests = AjaxHelpers["requests"](this)

                @view.render()
                @view.upload()
                expect(@model.get("uploading")).toBeTruthy()
                expect(requests.length).toEqual(1)
                request = requests[0]
                expect(request.url).toEqual("/upload")
                expect(request.method).toEqual("POST")

                request.respond(200, {"Content-Type": "application/json"},
                        '{"response": "dummy_response"}')
                expect(@model.get("uploading")).toBeFalsy()
                expect(@model.get("finished")).toBeTruthy()
                expect(@dialogResponse.pop()).toEqual("dummy_response")

            it "can handle upload errors", ->
                requests = AjaxHelpers["requests"](this)

                @view.render()
                @view.upload()
                requests[0].respond(500)
                expect(@model.get("title")).toMatch(/error/)
                expect(@view.remove).not.toHaveBeenCalled()

            it "removes itself after two seconds on successful upload", ->
                requests = AjaxHelpers["requests"](this)

                @view.render()
                @view.upload()
                requests[0].respond(200, {"Content-Type": "application/json"},
                        '{"response": "dummy_response"}')
                expect(modal_helpers.isShowingModal(@view)).toBeTruthy();
                @clock.tick(2001)
                expect(modal_helpers.isShowingModal(@view)).toBeFalsy();
