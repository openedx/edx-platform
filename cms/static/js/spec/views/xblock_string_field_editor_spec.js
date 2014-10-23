define(["jquery", "js/common_helpers/ajax_helpers", "js/common_helpers/template_helpers",
        "js/spec_helpers/edit_helpers", "js/models/xblock_info", "js/views/xblock_string_field_editor"],
       function ($, AjaxHelpers, TemplateHelpers, EditHelpers, XBlockInfo, XBlockStringFieldEditor) {
           describe("XBlockStringFieldEditorView", function () {
               var initialValue, updatedValue, getXBlockInfo, getFieldEditorView,
                   maxLabelLength, longValue;

               maxLabelLength = 10;
               longValue = '....v....x....v....x';
               initialValue = "Default Value";
               updatedValue = "Updated Value";

               getXBlockInfo = function (displayName) {
                   return new XBlockInfo(
                       {
                           display_name: displayName,
                           id: "my_xblock"
                       },
                       { parse: true }
                   );
               };

               getFieldEditorView = function (xblockInfo, options) {
                   if (xblockInfo === undefined) {
                       xblockInfo = getXBlockInfo(initialValue);
                   }
                   options = _.extend({}, _.extend(options || {}, _.extend({
                       model: xblockInfo,
                       el: $('.wrapper-xblock-field')
                   })))
                   return new XBlockStringFieldEditor(options);
               };

               beforeEach(function () {
                   TemplateHelpers.installTemplate('xblock-string-field-editor');
                   appendSetFixtures(
                           '<div class="wrapper-xblock-field incontext-editor is-editable"' +
                           'data-field="display_name" data-field-display-name="Display Name">' +
                           '<h1 class="page-header-title xblock-field-value incontext-editor-value">' +
                           '<span class="title-value">' + initialValue + '</span>' +
                           '</h1>' +
                           '</div>'
                   );
               });

               describe('Editing', function () {
                   var expectPostedNewDisplayName, expectEditCanceled;

                   expectPostedNewDisplayName = function (requests, displayName) {
                       AjaxHelpers.expectJsonRequest(requests, 'POST', '/xblock/my_xblock', {
                           metadata: {
                               display_name: displayName
                           }
                       });
                   };

                   expectEditCanceled = function (test, fieldEditorView, options) {
                       var requests, initialRequests, displayNameInput;
                       requests = AjaxHelpers.requests(test);
                       initialRequests = requests.length;
                       displayNameInput = EditHelpers.inlineEdit(fieldEditorView.$el, options.newTitle);
                       if (options.pressEscape) {
                           displayNameInput.simulate("keydown", { keyCode: $.simulate.keyCode.ESCAPE });
                           displayNameInput.simulate("keyup", { keyCode: $.simulate.keyCode.ESCAPE });
                       } else if (options.clickCancel) {
                           fieldEditorView.$('button[name=cancel]').click();
                       } else {
                           displayNameInput.change();
                       }
                       // No requests should be made when the edit is cancelled client-side
                       expect(initialRequests).toBe(requests.length);
                       EditHelpers.verifyInlineEditChange(fieldEditorView.$el, initialValue);
                       expect(fieldEditorView.model.get('display_name')).toBe(initialValue);
                   };

                   it('can inline edit the value', function () {
                       var requests, fieldEditorView;
                       requests = AjaxHelpers.requests(this);
                       fieldEditorView = getFieldEditorView().render();
                       EditHelpers.inlineEdit(fieldEditorView.$el, updatedValue);
                       fieldEditorView.$('button[name=submit]').click();
                       expectPostedNewDisplayName(requests, updatedValue);
                       // This is the response for the change operation.
                       AjaxHelpers.respondWithJson(requests, { });
                       // This is the response for the subsequent fetch operation.
                       AjaxHelpers.respondWithJson(requests, {display_name:  updatedValue});
                       EditHelpers.verifyInlineEditChange(fieldEditorView.$el, updatedValue);
                   });

                   it('does not change the title when a value update fails', function () {
                       var requests, fieldEditorView, initialRequests;
                       requests = AjaxHelpers.requests(this);
                       initialRequests = requests.length;
                       fieldEditorView = getFieldEditorView().render();
                       EditHelpers.inlineEdit(fieldEditorView.$el, updatedValue);
                       fieldEditorView.$('button[name=submit]').click();
                       expectPostedNewDisplayName(requests, updatedValue);
                       AjaxHelpers.respondWithError(requests);
                       // No fetch operation should occur.
                       expect(initialRequests + 1).toBe(requests.length);
                       EditHelpers.verifyInlineEditChange(fieldEditorView.$el, initialValue, updatedValue);
                   });

                   it('trims whitespace from the value', function () {
                       var requests, fieldEditorView;
                       requests = AjaxHelpers.requests(this);
                       fieldEditorView = getFieldEditorView().render();
                       updatedValue += ' ';
                       EditHelpers.inlineEdit(fieldEditorView.$el, updatedValue);
                       fieldEditorView.$('button[name=submit]').click();
                       expectPostedNewDisplayName(requests, updatedValue.trim());
                       // This is the response for the change operation.
                       AjaxHelpers.respondWithJson(requests, { });
                       // This is the response for the subsequent fetch operation.
                       AjaxHelpers.respondWithJson(requests, {display_name:  updatedValue.trim()});
                       EditHelpers.verifyInlineEditChange(fieldEditorView.$el, updatedValue.trim());
                   });

                   it('does not change the title when input is the empty string', function () {
                       var fieldEditorView = getFieldEditorView().render();
                       expectEditCanceled(this, fieldEditorView, {newTitle: ''});
                   });

                   it('does not change the title when input is whitespace-only', function () {
                       var fieldEditorView = getFieldEditorView().render();
                       expectEditCanceled(this, fieldEditorView, {newTitle: ' '});
                   });

                   it('can cancel an inline edit by pressing escape', function () {
                       var fieldEditorView = getFieldEditorView().render();
                       expectEditCanceled(this, fieldEditorView, {newTitle: updatedValue, pressEscape: true});
                   });

                   it('can cancel an inline edit by clicking cancel', function () {
                       var fieldEditorView = getFieldEditorView().render();
                       expectEditCanceled(this, fieldEditorView, {newTitle: updatedValue, clickCancel: true});
                   });

                   it('shows a truncated label when inline editing with a long value', function () {
                       var requests, view;
                       requests = AjaxHelpers.requests(this);
                       view = getFieldEditorView(getXBlockInfo(initialValue), { maxLabelLength: maxLabelLength });
                       view.render();
                       EditHelpers.inlineEdit(view.$el, longValue);
                       view.$('button[name=submit]').click();
                       // This is the response for the change operation.
                       AjaxHelpers.respondWithJson(requests, { });
                       // This is the response for the subsequent fetch operation.
                       AjaxHelpers.respondWithJson(requests, {display_name:  longValue});
                       expect(view.$('.xblock-field-value').html().length).toBe(maxLabelLength);
                   });
               });

               describe('Rendering', function () {
                   var expectInputMatchesModelDisplayName;

                   expectInputMatchesModelDisplayName = function (displayName) {
                       var fieldEditorView = getFieldEditorView(getXBlockInfo(displayName)).render();
                       expect(fieldEditorView.$('.xblock-field-input').val()).toBe(displayName);
                   };

                   it('renders single quotes in input field', function () {
                       expectInputMatchesModelDisplayName('Updated \'Display Name\'');
                   });

                   it('renders double quotes in input field', function () {
                       expectInputMatchesModelDisplayName('Updated "Display Name"');
                   });

                   it('renders open angle bracket in input field', function () {
                       expectInputMatchesModelDisplayName(updatedValue + '<');
                   });

                   it('renders close angle bracket in input field', function () {
                       expectInputMatchesModelDisplayName('>' + updatedValue);
                   });

                   it('truncates labels when they are too long', function () {
                       var longLabel = '....v....x....v....x',
                           view;
                       view = getFieldEditorView(getXBlockInfo(longLabel), { maxLabelLength: maxLabelLength });
                       view.render();
                       expect(view.$('.xblock-field-value').html().length).toBe(maxLabelLength);
                   });
               });
           });
       });
