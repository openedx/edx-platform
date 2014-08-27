define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/view_helpers", "js/spec_helpers/edit_helpers", "js/models/xblock_info", "js/views/xblock_string_field_editor"],
       function ($, create_sinon, view_helpers, edit_helpers, XBlockInfo, XBlockStringFieldEditor) {
           describe("XBlockStringFieldEditorView", function () {
               var initialDisplayName, updatedDisplayName, getXBlockInfo, getFieldEditorView;

               getXBlockInfo = function (displayName) {
                   return new XBlockInfo(
                       {
                           display_name: displayName,
                           id: "my_xblock"
                       },
                       { parse: true }
                   );
               };

               getFieldEditorView = function (xblockInfo) {
                   if (xblockInfo === undefined) {
                       xblockInfo = getXBlockInfo(initialDisplayName);
                   }
                   return new XBlockStringFieldEditor({
                       model: xblockInfo,
                       el: $('.wrapper-xblock-field')
                   });
               };

               beforeEach(function () {
                   initialDisplayName = "Default Display Name";
                   updatedDisplayName = "Updated Display Name";
                   view_helpers.installTemplate('xblock-string-field-editor');
                   appendSetFixtures(
                           '<div class="wrapper-xblock-field incontext-editor is-editable"' +
                           'data-field="display_name" data-field-display-name="Display Name">' +
                           '<h1 class="page-header-title xblock-field-value incontext-editor-value"><span class="title-value">' + initialDisplayName + '</span></h1>' +
                           '</div>'
                   );
               });

               describe('Editing', function () {
                   var expectPostedNewDisplayName, expectEditCanceled;

                   expectPostedNewDisplayName = function (requests, displayName) {
                       create_sinon.expectJsonRequest(requests, 'POST', '/xblock/my_xblock', {
                           metadata: {
                               display_name: displayName
                           }
                       });
                   };

                   expectEditCanceled = function (test, fieldEditorView, options) {
                       var requests, initialRequests, displayNameInput;
                       requests = create_sinon.requests(test);
                       initialRequests = requests.length;
                       displayNameInput = edit_helpers.inlineEdit(fieldEditorView.$el, options.newTitle);
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
                       edit_helpers.verifyInlineEditChange(fieldEditorView.$el, initialDisplayName);
                       expect(fieldEditorView.model.get('display_name')).toBe(initialDisplayName);
                   };

                   it('can inline edit the display name', function () {
                       var requests, fieldEditorView;
                       requests = create_sinon.requests(this);
                       fieldEditorView = getFieldEditorView().render();
                       edit_helpers.inlineEdit(fieldEditorView.$el, updatedDisplayName);
                       fieldEditorView.$('button[name=submit]').click();
                       expectPostedNewDisplayName(requests, updatedDisplayName);
                       // This is the response for the change operation.
                       create_sinon.respondWithJson(requests, { });
                       // This is the response for the subsequent fetch operation.
                       create_sinon.respondWithJson(requests, {display_name:  updatedDisplayName});
                       edit_helpers.verifyInlineEditChange(fieldEditorView.$el, updatedDisplayName);
                   });

                   it('does not change the title when a display name update fails', function () {
                       var requests, fieldEditorView, initialRequests;
                       requests = create_sinon.requests(this);
                       initialRequests = requests.length;
                       fieldEditorView = getFieldEditorView().render();
                       edit_helpers.inlineEdit(fieldEditorView.$el, updatedDisplayName);
                       fieldEditorView.$('button[name=submit]').click();
                       expectPostedNewDisplayName(requests, updatedDisplayName);
                       create_sinon.respondWithError(requests);
                       // No fetch operation should occur.
                       expect(initialRequests + 1).toBe(requests.length);
                       edit_helpers.verifyInlineEditChange(fieldEditorView.$el, initialDisplayName, updatedDisplayName);
                   });

                   it('trims whitespace from the display name', function () {
                       var requests, fieldEditorView;
                       requests = create_sinon.requests(this);
                       fieldEditorView = getFieldEditorView().render();
                       updatedDisplayName += ' ';
                       edit_helpers.inlineEdit(fieldEditorView.$el, updatedDisplayName);
                       fieldEditorView.$('button[name=submit]').click();
                       expectPostedNewDisplayName(requests, updatedDisplayName.trim());
                       // This is the response for the change operation.
                       create_sinon.respondWithJson(requests, { });
                       // This is the response for the subsequent fetch operation.
                       create_sinon.respondWithJson(requests, {display_name:  updatedDisplayName.trim()});
                       edit_helpers.verifyInlineEditChange(fieldEditorView.$el, updatedDisplayName.trim());
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
                       expectEditCanceled(this, fieldEditorView, {newTitle: updatedDisplayName, pressEscape: true});
                   });

                   it('can cancel an inline edit by clicking cancel', function () {
                       var fieldEditorView = getFieldEditorView().render();
                       expectEditCanceled(this, fieldEditorView, {newTitle: updatedDisplayName, clickCancel: true});
                   });
               });

               describe('Rendering', function () {
                   var expectInputMatchesModelDisplayName = function (displayName) {
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
                       expectInputMatchesModelDisplayName(updatedDisplayName + '<');
                   });

                   it('renders close angle bracket in input field', function () {
                       expectInputMatchesModelDisplayName('>' + updatedDisplayName);
                   });
               });
           });
       });
