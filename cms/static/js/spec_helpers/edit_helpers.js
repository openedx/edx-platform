/**
 * Provides helper methods for invoking Studio editors in Jasmine tests.
 */
import $ from 'jquery';
import _ from 'underscore';
import AjaxHelpers from 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers';
import TemplateHelpers from 'common/js/spec_helpers/template_helpers';
import modal_helpers from 'js/spec_helpers/modal_helpers';
import EditXBlockModal from 'js/views/modals/edit_xblock';
import ComponentTemplates from 'js/collections/component_template';
import XModule from 'xmodule/js/src/xmodule';
import 'cms/js/main';
import 'xblock/cms.runtime.v1';

// eslint-disable-next-line import/no-mutable-exports
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
        type: 'discussion',
        support_legend: {show_legend: false}
    }, {
        templates: [
            {
                category: 'html',
                boilerplate_name: null,
                display_name: 'Text'
            }, {
                category: 'html',
                boilerplate_name: 'announcement.yaml',
                display_name: 'Announcement'
            }, {
                category: 'html',
                boilerplate_name: 'raw.yaml',
                display_name: 'Raw HTML'
            }],
        type: 'html',
        support_legend: {show_legend: false}
    }],
{
    parse: true
});

installEditTemplates = function(append) {
    modal_helpers.installModalTemplates(append);

    // Add templates needed by the add XBlock menu
    TemplateHelpers.installTemplate('add-xblock-component');
    TemplateHelpers.installTemplate('add-xblock-component-button');
    TemplateHelpers.installTemplate('add-xblock-component-menu');
    TemplateHelpers.installTemplate('add-xblock-component-menu-problem');
    TemplateHelpers.installTemplate('add-xblock-component-support-legend');
    TemplateHelpers.installTemplate('add-xblock-component-support-level');

    // Add templates needed by the edit XBlock modal
    TemplateHelpers.installTemplate('edit-xblock-modal');
    TemplateHelpers.installTemplate('editor-mode-button');
    TemplateHelpers.installTemplate('edit-title-button');
    TemplateHelpers.installTemplate('edit-upstream-alert');

    // Add templates needed by the settings editor
    TemplateHelpers.installTemplate('metadata-editor');
    TemplateHelpers.installTemplate('metadata-number-entry', false, 'metadata-number-entry');
    TemplateHelpers.installTemplate('metadata-string-entry', false, 'metadata-string-entry');
};

showEditModal = function(requests, xblockElement, model, mockHtml, options) {
    var modal = new EditXBlockModal({});
    modal.edit(xblockElement, model, options);
    AjaxHelpers.respondWithJson(requests, {
        html: mockHtml,
        resources: []
    });
    return modal;
};

verifyXBlockRequest = function(requests, expectedJson) {
    var request = AjaxHelpers.currentRequest(requests),
        actualJson = JSON.parse(request.requestBody);
    expect(request.url).toEqual('/xblock/');
    expect(request.method).toEqual('POST');
    expect(actualJson).toEqual(expectedJson);
};

// eslint-disable-next-line import/no-mutable-exports
var editHelpers = $.extend(modal_helpers, {
    installMockXBlock: installMockXBlock,
    uninstallMockXBlock: uninstallMockXBlock,
    installMockXModule: installMockXModule,
    uninstallMockXModule: uninstallMockXModule,
    mockComponentTemplates: mockComponentTemplates,
    installEditTemplates: installEditTemplates,
    showEditModal: showEditModal,
    verifyXBlockRequest: verifyXBlockRequest
});

export default editHelpers;

export {
    installMockXBlock,
    uninstallMockXBlock,
    installMockXModule,
    uninstallMockXModule,
    mockComponentTemplates,
    installEditTemplates,
    showEditModal,
    verifyXBlockRequest,
};
