define([ "jquery", "underscore", "js/spec_helpers/create_sinon", "js/spec_helpers/edit_helpers",
    "js/views/xblock_editor", "js/models/xblock_info"],
    function ($, _, create_sinon, edit_helpers, XBlockEditorView, XBlockInfo) {

        describe("XBlockEditorView", function() {
            var model, editor, testDisplayName, mockSaveResponse;

            testDisplayName = 'Test Display Name';
            mockSaveResponse = {
                data: "<p>Some HTML</p>",
                metadata: {
                    display_name: testDisplayName
                }
            };

            beforeEach(function () {
                edit_helpers.installEditTemplates();
                model = new XBlockInfo({
                    id: 'testCourse/branch/draft/block/verticalFFF',
                    display_name: 'Test Unit',
                    category: 'vertical'
                });
                editor = new XBlockEditorView({
                    model: model
                });
            });

            describe("Editing an xblock", function() {
                var mockXBlockEditorHtml;

                beforeEach(function () {
                    edit_helpers.installMockXBlock();
                });

                afterEach(function() {
                    edit_helpers.uninstallMockXBlock();
                });

                mockXBlockEditorHtml = readFixtures('mock/mock-xblock-editor.underscore');

                it('can render itself', function() {
                    var requests = create_sinon.requests(this);
                    editor.render();
                    create_sinon.respondWithJson(requests, {
                        html: mockXBlockEditorHtml,
                        resources: []
                    });

                    expect(editor.$el.select('.xblock-header')).toBeTruthy();
                    expect(editor.getMode()).toEqual('settings');
                });
            });

            describe("Editing an xmodule", function() {
                var mockXModuleEditorHtml;

                mockXModuleEditorHtml = readFixtures('mock/mock-xmodule-editor.underscore');

                beforeEach(function() {
                    edit_helpers.installMockXModule(mockSaveResponse);
                });

                afterEach(function () {
                    edit_helpers.uninstallMockXModule();
                });

                it('can render itself', function() {
                    var requests = create_sinon.requests(this);
                    editor.render();
                    create_sinon.respondWithJson(requests, {
                        html: mockXModuleEditorHtml,
                        resources: []
                    });

                    expect(editor.$el.select('.xblock-header')).toBeTruthy();
                    expect(editor.getMode()).toEqual('editor');
                });

                it('saves any custom metadata', function() {
                    var requests = create_sinon.requests(this), request, response;
                    editor.render();
                    create_sinon.respondWithJson(requests, {
                        html: mockXModuleEditorHtml,
                        resources: []
                    });
                    // Give the mock xblock a save method...
                    editor.xblock.save = window.MockDescriptor.save;
                    editor.model.save(editor.getXModuleData());
                    request = requests[requests.length - 1];
                    response = JSON.parse(request.requestBody);
                    expect(response.metadata.display_name).toBe(testDisplayName);
                    expect(response.metadata.custom_field).toBe('Custom Value');
                });

                it('can render a module with only settings', function() {
                    var requests = create_sinon.requests(this), mockXModuleEditorHtml;
                    mockXModuleEditorHtml = readFixtures('mock/mock-xmodule-settings-only-editor.underscore');

                    editor.render();
                    create_sinon.respondWithJson(requests, {
                        html: mockXModuleEditorHtml,
                        resources: []
                    });

                    expect(editor.$el.select('.xblock-header')).toBeTruthy();
                    expect(editor.getMode()).toEqual('settings');
                });
            });
        });
    });
