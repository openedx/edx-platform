(function(CMS, sinon) {
    'use strict';
    define(['js/models/uploads', 'js/views/uploads', 'js/models/chapter',
            'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers', 'js/spec_helpers/modal_helpers'],
            function(FileUpload, UploadDialog, Chapter, AjaxHelpers, modal_helpers) {
        describe('UploadDialog', function() {
            var createTestView, tpl;
            tpl = readFixtures('upload-dialog.underscore');
            beforeEach(function() {
                var dialogResponse;
                modal_helpers.installModalTemplates();
                appendSetFixtures($("<script>", {
                    id: 'upload-dialog-tpl',
                    type: 'text/template'
                }).text(tpl));
                CMS.URL.UPLOAD_ASSET = '/upload';
                this.model = new FileUpload({
                    mimeTypes: ['application/pdf']
                });
                this.dialogResponse = dialogResponse = [];
                this.mockFiles = [];
            });
            afterEach(function() {
                delete CMS.URL.UPLOAD_ASSET;
                modal_helpers.cancelModalIfShowing();
            });
            createTestView = function(test) {
                var jqMockFileInput, mockFileInput, originalView$, view;
                view = new UploadDialog({
                    model: test.model,
                    url: CMS.URL.UPLOAD_ASSET,
                    onSuccess: function(response) {
                        return test.dialogResponse.push(response.response);
                    }
                });
                spyOn(view, 'remove').and.callThrough();
                mockFileInput = jasmine.createSpy('mockFileInput');
                mockFileInput.files = test.mockFiles;
                jqMockFileInput = jasmine.createSpyObj('jqMockFileInput', ['get', 'replaceWith']);
                jqMockFileInput.get.and.returnValue(mockFileInput);
                originalView$ = view.$;
                spyOn(view, "$").and.callFake(function(selector) {
                    if (selector === "input[type=file]") {
                        return jqMockFileInput;
                    } else {
                        return originalView$.apply(this, arguments);
                    }
                });
                return view;
            };
            describe("Basic", function() {
                it("should render without a file selected", function() {
                    var view;
                    view = createTestView(this);
                    view.render();
                    expect(view.$el).toContainElement("input[type=file]");
                    expect(view.$(".action-upload")).toHaveClass("disabled");
                });
                it("should render with a PDF selected", function() {
                    var file, view;
                    view = createTestView(this);
                    file = {
                        name: "fake.pdf",
                        "type": "application/pdf"
                    };
                    this.mockFiles.push(file);
                    this.model.set("selectedFile", file);
                    view.render();
                    expect(view.$el).toContainElement("input[type=file]");
                    expect(view.$el).not.toContainElement("#upload_error");
                    expect(view.$(".action-upload")).not.toHaveClass("disabled");
                });
                it("should render an error with an invalid file type selected", function() {
                    var file, view;
                    view = createTestView(this);
                    file = {
                        name: "fake.png",
                        "type": "image/png"
                    };
                    this.mockFiles.push(file);
                    this.model.set("selectedFile", file);
                    view.render();
                    expect(view.$el).toContainElement("input[type=file]");
                    expect(view.$el).toContainElement("#upload_error");
                    expect(view.$(".action-upload")).toHaveClass("disabled");
                });
                it("should render an error with an invalid file type after a correct file type selected", function() {
                    var correctFile, event, inCorrectFile, realMethod, view;
                    view = createTestView(this);
                    correctFile = {
                        name: "fake.pdf",
                        "type": "application/pdf"
                    };
                    inCorrectFile = {
                        name: "fake.png",
                        "type": "image/png"
                    };
                    event = {};
                    view.render();
                    event.target = {
                        "files": [correctFile]
                    };
                    view.selectFile(event);
                    expect(view.$el).toContainElement("input[type=file]");
                    expect(view.$el).not.toContainElement("#upload_error");
                    expect(view.$(".action-upload")).not.toHaveClass("disabled");
                    realMethod = this.model.set;
                    spyOn(this.model, "set").and.callFake(function(data) {
                        if (data.selectedFile !== void 0) {
                            this.attributes.selectedFile = data.selectedFile;
                            this.changed = {};
                            return this.changed;
                        } else {
                            return realMethod.apply(this, arguments);
                        }
                    });
                    event.target = {
                        "files": [inCorrectFile]
                    };
                    view.selectFile(event);
                    expect(view.$el).toContainElement("input[type=file]");
                    expect(view.$el).toContainElement("#upload_error");
                    expect(view.$(".action-upload")).toHaveClass("disabled");
                });
            });
            describe("Uploads", function() {
                beforeEach(function() {
                    this.clock = sinon.useFakeTimers();
                });
                afterEach(function() {
                    modal_helpers.cancelModalIfShowing();
                    this.clock.restore();
                });
                it("can upload correctly", function() {
                    var requests, view;
                    requests = AjaxHelpers.requests(this);
                    view = createTestView(this);
                    view.render();
                    view.upload();
                    expect(this.model.get("uploading")).toBeTruthy();
                    AjaxHelpers.expectRequest(requests, "POST", "/upload");
                    AjaxHelpers.respondWithJson(requests, {
                        response: "dummy_response"
                    });
                    expect(this.model.get("uploading")).toBeFalsy();
                    expect(this.model.get("finished")).toBeTruthy();
                    expect(this.dialogResponse.pop()).toEqual("dummy_response");
                });
                it("can handle upload errors", function() {
                    var requests, view;
                    requests = AjaxHelpers.requests(this);
                    view = createTestView(this);
                    view.render();
                    view.upload();
                    AjaxHelpers.respondWithError(requests);
                    expect(this.model.get("title")).toMatch(/error/);
                    expect(view.remove).not.toHaveBeenCalled();
                });
                it("removes itself after two seconds on successful upload", function() {
                    var requests, view;
                    requests = AjaxHelpers.requests(this);
                    view = createTestView(this);
                    view.render();
                    view.upload();
                    AjaxHelpers.respondWithJson(requests, {
                        response: "dummy_response"
                    });
                    expect(modal_helpers.isShowingModal(view)).toBeTruthy();
                    this.clock.tick(2001);
                    expect(modal_helpers.isShowingModal(view)).toBeFalsy();
                });
            });
        });
    });

}).call(this, CMS, sinon);  //jshint ignore:line
