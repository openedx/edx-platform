define ["js/models/uploads", "js/views/uploads", "js/models/chapter",
        "edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers", "js/spec_helpers/modal_helpers"],
    (FileUpload, UploadDialog, Chapter, AjaxHelpers, modal_helpers) ->

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
                @mockFiles = []

            afterEach ->
                delete CMS.URL.UPLOAD_ASSET
                modal_helpers.cancelModalIfShowing()

            createTestView = (test) ->
                view = new UploadDialog(
                    model: test.model,
                    url:  CMS.URL.UPLOAD_ASSET,
                    onSuccess: (response) =>
                        test.dialogResponse.push(response.response)
                )
                spyOn(view, 'remove').and.callThrough()

                # create mock file input, so that we aren't subject to browser restrictions
                mockFileInput = jasmine.createSpy('mockFileInput')
                mockFileInput.files = test.mockFiles
                jqMockFileInput = jasmine.createSpyObj('jqMockFileInput', ['get', 'replaceWith'])
                jqMockFileInput.get.and.returnValue(mockFileInput)
                originalView$ = view.$
                spyOn(view, "$").and.callFake (selector) ->
                    if selector == "input[type=file]"
                        jqMockFileInput
                    else
                        originalView$.apply(this, arguments)
                @lastView = view

            describe "Basic", ->
                it "should render without a file selected", ->
                    view = createTestView(this)
                    view.render()
                    expect(view.$el).toContainElement("input[type=file]")
                    expect(view.$(".action-upload")).toHaveClass("disabled")

                it "should render with a PDF selected", ->
                    view = createTestView(this)
                    file = {name: "fake.pdf", "type": "application/pdf"}
                    @mockFiles.push(file)
                    @model.set("selectedFile", file)
                    view.render()
                    expect(view.$el).toContainElement("input[type=file]")
                    expect(view.$el).not.toContainElement("#upload_error")
                    expect(view.$(".action-upload")).not.toHaveClass("disabled")

                it "should render an error with an invalid file type selected", ->
                    view = createTestView(this)
                    file = {name: "fake.png", "type": "image/png"}
                    @mockFiles.push(file)
                    @model.set("selectedFile", file)
                    view.render()
                    expect(view.$el).toContainElement("input[type=file]")
                    expect(view.$el).toContainElement("#upload_error")
                    expect(view.$(".action-upload")).toHaveClass("disabled")

                it "should render an error with an invalid file type after a correct file type selected", ->
                    view = createTestView(this)
                    correctFile = {name: "fake.pdf", "type": "application/pdf"}
                    inCorrectFile = {name: "fake.png", "type": "image/png"}
                    event = {}
                    view.render()

                    event.target = {"files": [correctFile]}
                    view.selectFile(event)
                    expect(view.$el).toContainElement("input[type=file]")
                    expect(view.$el).not.toContainElement("#upload_error")
                    expect(view.$(".action-upload")).not.toHaveClass("disabled")

                    realMethod = @model.set
                    spyOn(@model, "set").and.callFake (data) ->
                        if data.selectedFile != undefined
                            this.attributes.selectedFile = data.selectedFile
                            this.changed = {}
                        else
                            realMethod.apply(this, arguments)

                    event.target = {"files": [inCorrectFile]}
                    view.selectFile(event)
                    expect(view.$el).toContainElement("input[type=file]")
                    expect(view.$el).toContainElement("#upload_error")
                    expect(view.$(".action-upload")).toHaveClass("disabled")

            describe "Uploads", ->
                beforeEach ->
                    @clock = sinon.useFakeTimers()

                afterEach ->
                    modal_helpers.cancelModalIfShowing()
                    @clock.restore()

                it "can upload correctly", ->
                    requests = AjaxHelpers.requests(this);
                    view = createTestView(this)
                    view.render()
                    view.upload()
                    expect(@model.get("uploading")).toBeTruthy()
                    AjaxHelpers.expectRequest(requests, "POST", "/upload")
                    AjaxHelpers.respondWithJson(requests, { response: "dummy_response"})
                    expect(@model.get("uploading")).toBeFalsy()
                    expect(@model.get("finished")).toBeTruthy()
                    expect(@dialogResponse.pop()).toEqual("dummy_response")

                it "can handle upload errors", ->
                    requests = AjaxHelpers.requests(this);
                    view = createTestView(this)
                    view.render()
                    view.upload()
                    AjaxHelpers.respondWithError(requests)
                    expect(@model.get("title")).toMatch(/error/)
                    expect(view.remove).not.toHaveBeenCalled()

                it "removes itself after two seconds on successful upload", ->
                    requests = AjaxHelpers.requests(this);
                    view = createTestView(this)
                    view.render()
                    view.upload()
                    AjaxHelpers.respondWithJson(requests, { response: "dummy_response"})
                    expect(modal_helpers.isShowingModal(view)).toBeTruthy();
                    @clock.tick(2001)
                    expect(modal_helpers.isShowingModal(view)).toBeFalsy();
