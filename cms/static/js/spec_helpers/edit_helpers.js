/**
 * Provides helper methods for invoking Studio editors in Jasmine tests.
 */
define(["jquery", "underscore", "js/spec_helpers/create_sinon", "js/spec_helpers/modal_helpers",
    "js/views/modals/edit_xblock", "js/collections/component_template",
    "xmodule", "coffee/src/main", "xblock/cms.runtime.v1"],
    function($, _, create_sinon, modal_helpers, EditXBlockModal, ComponentTemplates) {

        var installMockXBlock, uninstallMockXBlock, installMockXModule, uninstallMockXModule,
            mockComponentTemplates, installEditTemplates, showEditModal, verifyXBlockRequest;

        installMockXBlock = function(mockResult) {
            window.MockXBlock = function(runtime, element) {
                var block = {
                    runtime: runtime
                };
                if (mockResult) {
                    block.save = function() {
                        return mockResult;
                    };
                }
                return block;
            };
        };

        uninstallMockXBlock = function() {
            window.MockXBlock = null;
        };

        installMockXModule = function(mockResult) {
            window.MockDescriptor = _.extend(XModule.Descriptor, {
                save: function() {
                    return mockResult;
                }
            });
        };

        uninstallMockXModule = function() {
            window.MockDescriptor = null;
        };

        mockComponentTemplates = new ComponentTemplates([
            {
                templates: [
                    {
                        category: 'discussion',
                        display_name: 'Discussion'
                    }],
                type: 'discussion'
            }, {
                "templates": [
                    {
                        "category": "html",
                        "boilerplate_name": null,
                        "display_name": "Text"
                    }, {
                        "category": "html",
                        "boilerplate_name": "announcement.yaml",
                        "display_name": "Announcement"
                    }, {
                        "category": "html",
                        "boilerplate_name": "raw.yaml",
                        "display_name": "Raw HTML"
                    }],
                "type": "html"
            }],
            {
                parse: true
            });

        installEditTemplates = function(append) {
            modal_helpers.installModalTemplates(append);

            // Add templates needed by the add XBlock menu
            modal_helpers.installTemplate('add-xblock-component');
            modal_helpers.installTemplate('add-xblock-component-button');
            modal_helpers.installTemplate('add-xblock-component-menu');
            modal_helpers.installTemplate('add-xblock-component-menu-problem');

            // Add templates needed by the edit XBlock modal
            modal_helpers.installTemplate('edit-xblock-modal');
            modal_helpers.installTemplate('editor-mode-button');

            // Add templates needed by the settings editor
            modal_helpers.installTemplate('metadata-editor');
            modal_helpers.installTemplate('metadata-number-entry');
            modal_helpers.installTemplate('metadata-string-entry');
        };

        showEditModal = function(requests, xblockElement, model, mockHtml, options) {
            var modal = new EditXBlockModal({});
            modal.edit(xblockElement, model, options);
            create_sinon.respondWithJson(requests, {
                html: mockHtml,
                "resources": []
            });
            return modal;
        };

        verifyXBlockRequest = function (requests, expectedJson) {
            var request = requests[requests.length - 1],
                actualJson = JSON.parse(request.requestBody);
            expect(request.url).toEqual("/xblock/");
            expect(request.method).toEqual("POST");
            expect(actualJson).toEqual(expectedJson);
        };

        return $.extend(modal_helpers, {
            'installMockXBlock': installMockXBlock,
            'uninstallMockXBlock': uninstallMockXBlock,
            'installMockXModule': installMockXModule,
            'uninstallMockXModule': uninstallMockXModule,
            'mockComponentTemplates': mockComponentTemplates,
            'installEditTemplates': installEditTemplates,
            'showEditModal': showEditModal,
            'verifyXBlockRequest': verifyXBlockRequest
        });
    });
