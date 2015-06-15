define(['backbone', 'jquery', 'underscore', 'common/js/spec_helpers/ajax_helpers', 'common/js/spec_helpers/template_helpers',
        'js/views/fields',
        'js/spec/views/fields_helpers',
        'string_utils'],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, FieldViews, FieldViewsSpecHelpers) {
        'use strict';

        var USERNAME = 'Legolas',
            BIO = "My Name is Theon Greyjoy. I'm member of House Greyjoy";

        describe("edx.FieldViews", function () {

            var requests,
                timerCallback;

            var fieldViewClasses = [
                FieldViews.ReadonlyFieldView,
                FieldViews.TextFieldView,
                FieldViews.DropdownFieldView,
                FieldViews.LinkFieldView,
                FieldViews.TextareaFieldView

            ];

            beforeEach(function () {
                TemplateHelpers.installTemplate('templates/fields/field_readonly');
                TemplateHelpers.installTemplate('templates/fields/field_dropdown');
                TemplateHelpers.installTemplate('templates/fields/field_link');
                TemplateHelpers.installTemplate('templates/fields/field_text');
                TemplateHelpers.installTemplate('templates/fields/field_textarea');

                timerCallback = jasmine.createSpy('timerCallback');
                jasmine.Clock.useMock();
            });

            it("updates messages correctly for all fields", function() {

                for (var i = 0; i < fieldViewClasses.length; i++) {

                    var fieldViewClass = fieldViewClasses[i];
                    var fieldData = FieldViewsSpecHelpers.createFieldData(fieldViewClass, {
                        title: 'Username',
                        valueAttribute: 'username',
                        helpMessage: 'The username that you use to sign in to edX.'
                    });

                    var view = new fieldViewClass(fieldData).render();
                    FieldViewsSpecHelpers.verifyMessageUpdates(view, fieldData, timerCallback);
                }
            });

            it("resets to help message some time after success message is set", function() {

                for (var i = 0; i < fieldViewClasses.length; i++) {
                    var fieldViewClass = fieldViewClasses[i];
                    var fieldData = FieldViewsSpecHelpers.createFieldData(fieldViewClass, {
                        title: 'Username',
                        valueAttribute: 'username',
                        helpMessage: 'The username that you use to sign in to edX.'
                    });

                    var view = new fieldViewClass(fieldData).render();
                    FieldViewsSpecHelpers.verifySuccessMessageReset(view, fieldData, timerCallback);
                }
            });

            it("sends a PATCH request when saveAttributes is called", function() {

                requests = AjaxHelpers.requests(this);

                var fieldViewClass = FieldViews.EditableFieldView;
                var fieldData = FieldViewsSpecHelpers.createFieldData(fieldViewClass, {
                    title: 'Preferred Language',
                    valueAttribute: 'language',
                    helpMessage: 'Your preferred language.'
                });

                var view = new fieldViewClass(fieldData);
                view.saveAttributes(
                    {'language': 'ur'},
                    {'headers': {'Priority': 'Urgent'}}
                );

                var request = requests[0];
                expect(request.method).toBe('PATCH');
                expect(request.requestHeaders['Content-Type']).toBe('application/merge-patch+json;charset=utf-8');
                expect(request.requestHeaders.Priority).toBe('Urgent');
                expect(request.requestBody).toBe('{"language":"ur"}');
            });

            it("correctly renders and updates ReadonlyFieldView", function() {
                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.ReadonlyFieldView, {
                    title: 'Username',
                    valueAttribute: 'username',
                    helpMessage: 'The username that you use to sign in to edX.'
                });
                var view = new FieldViews.ReadonlyFieldView(fieldData).render();

                FieldViewsSpecHelpers.expectTitleAndMessageToContain(view, fieldData.title, fieldData.helpMessage, false);
                expect(view.$('.u-field-value input').val().trim()).toBe(USERNAME);

                view.model.set({'username': 'bookworm'});
                expect(view.$('.u-field-value input').val().trim()).toBe('bookworm');
            });

            it("correctly renders, updates and persists changes to TextFieldView when editable == always", function() {

                requests = AjaxHelpers.requests(this);

                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.TextFieldView, {
                    title: 'Full Name',
                    valueAttribute: 'name',
                    helpMessage: 'How are you?'
                });
                var view = new FieldViews.TextFieldView(fieldData).render();

                FieldViewsSpecHelpers.verifyTextField(view, {
                    title: fieldData.title,
                    valueAttribute: fieldData.valueAttribute,
                    helpMessage: fieldData.helpMessage,
                    validValue: 'My Name',
                    invalidValue1: 'Your Name',
                    invalidValue2: 'Her Name',
                    validationError: "Think again!",
                    defaultValue: ''
                }, requests);
            });

            it("correctly renders and updates DropdownFieldView when editable == never", function() {

                requests = AjaxHelpers.requests(this);

                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.DropdownFieldView, {
                    title: 'Full Name',
                    valueAttribute: 'name',
                    helpMessage: 'edX full name',
                    editable: 'never'

                });
                var view = new FieldViews.DropdownFieldView(fieldData).render();
                FieldViewsSpecHelpers.expectTitleAndMessageToContain(view, fieldData.title, fieldData.helpMessage, false);
                expect(view.el).toHaveClass('mode-hidden');

                view.model.set({'name': fieldData.options[1][0]});
                expect(view.el).toHaveClass('mode-display');
                view.$el.click();
                expect(view.el).toHaveClass('mode-display');
            });

            it("correctly renders, updates and persists changes to DropdownFieldView when editable == always", function() {

                requests = AjaxHelpers.requests(this);

                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.DropdownFieldView, {
                    title: 'Full Name',
                    valueAttribute: 'name',
                    helpMessage: 'edX full name'
                });
                var view = new FieldViews.DropdownFieldView(fieldData).render();

                FieldViewsSpecHelpers.verifyDropDownField(view, {
                    title: fieldData.title,
                    valueAttribute: fieldData.valueAttribute,
                    helpMessage: fieldData.helpMessage,
                    validValue: FieldViewsSpecHelpers.SELECT_OPTIONS[0][0],
                    invalidValue1: FieldViewsSpecHelpers.SELECT_OPTIONS[1][0],
                    invalidValue2: FieldViewsSpecHelpers.SELECT_OPTIONS[2][0],
                    validationError: "Nope, this will not do!",
                    defaultValue: null
                }, requests);
            });

            it("correctly renders, updates and persists changes to DropdownFieldView when editable == toggle", function() {

                requests = AjaxHelpers.requests(this);

                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.DropdownFieldView, {
                    title: 'Full Name',
                    valueAttribute: 'name',
                    helpMessage: 'edX full name',
                    editable: 'toggle'
                });
                var view = new FieldViews.DropdownFieldView(fieldData).render();

                FieldViewsSpecHelpers.verifyDropDownField(view, {
                    title: fieldData.title,
                    valueAttribute: fieldData.valueAttribute,
                    helpMessage: fieldData.helpMessage,
                    editable: 'toggle',
                    validValue: FieldViewsSpecHelpers.SELECT_OPTIONS[0][0],
                    invalidValue1: FieldViewsSpecHelpers.SELECT_OPTIONS[1][0],
                    invalidValue2: FieldViewsSpecHelpers.SELECT_OPTIONS[2][0],
                    validationError: "Nope, this will not do!",
                    defaultValue: null
                }, requests);
            });

            it("only shows empty option in DropdownFieldView if required is false or model value is not set", function() {
                requests = AjaxHelpers.requests(this);

                var editableOptions = ['toggle', 'always'];
                _.each(editableOptions, function(editable) {
                    var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.DropdownFieldView, {
                        title: 'Drop Down Field',
                        valueAttribute: 'drop-down',
                        helpMessage: 'edX drop down',
                        editable: editable,
                        required:true
                    });
                    var view = new FieldViews.DropdownFieldView(fieldData).render();

                    expect(view.modelValueIsSet()).toBe(false);
                    expect(view.displayValue()).toBe('');

                    if(editable === 'toggle') { view.showEditMode(true); }
                    view.$('.u-field-value > select').val(FieldViewsSpecHelpers.SELECT_OPTIONS[0]).change();
                    expect(view.fieldValue()).toBe(FieldViewsSpecHelpers.SELECT_OPTIONS[0][0]);

                    AjaxHelpers.respondWithNoContent(requests);
                    if(editable === 'toggle') { view.showEditMode(true); }
                    // When server returns success, there should no longer be an empty option.
                    expect($(view.$('.u-field-value option')[0]).val()).toBe('si');
                });
            });

            it("correctly renders and updates TextAreaFieldView when editable == never", function() {
                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.TextareaFieldView, {
                    title: 'About me',
                    valueAttribute: 'bio',
                    helpMessage: 'Wicked is good',
                    placeholderValue: "Tell other edX learners a little about yourself: where you live, " +
                        "what your interests are, why you’re taking courses on edX, or what you hope to learn.",
                    editable: 'never'
                });

                // set bio to empty to see the placeholder.
                fieldData.model.set({bio: ''});
                var view = new FieldViews.TextareaFieldView(fieldData).render();
                FieldViewsSpecHelpers.expectTitleAndMessageToContain(view, fieldData.title, fieldData.helpMessage, false);
                expect(view.el).toHaveClass('mode-hidden');
                expect(view.$('.u-field-value .u-field-value-readonly').text()).toBe(fieldData.placeholderValue);

                var bio = 'Too much to tell!';
                view.model.set({'bio': bio});
                expect(view.el).toHaveClass('mode-display');
                expect(view.$('.u-field-value .u-field-value-readonly').text()).toBe(bio);
                view.$el.click();
                expect(view.el).toHaveClass('mode-display');
            });

            it("correctly renders, updates and persists changes to TextAreaFieldView when editable == toggle", function() {

                requests = AjaxHelpers.requests(this);

                var valueInputSelector = '.u-field-value > textarea';
                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.TextareaFieldView, {
                    title: 'About me',
                    valueAttribute: 'bio',
                    helpMessage: 'Wicked is good',
                    placeholderValue: "Tell other edX learners a little about yourself: where you live, " +
                        "what your interests are, why you’re taking courses on edX, or what you hope to learn.",
                    editable: 'toggle'

                });
                fieldData.model.set({'bio': ''});

                var view = new FieldViews.TextareaFieldView(fieldData).render();

                FieldViewsSpecHelpers.expectTitleToContain(view, fieldData.title);
                FieldViewsSpecHelpers.expectMessageContains(view, view.indicators.canEdit);
                expect(view.el).toHaveClass('mode-placeholder');
                expect(view.$('.u-field-value .u-field-value-readonly').text()).toBe(fieldData.placeholderValue);

                view.$('.wrapper-u-field').click();
                expect(view.el).toHaveClass('mode-edit');
                view.$(valueInputSelector).val(BIO).focusout();
                expect(view.fieldValue()).toBe(BIO);
                AjaxHelpers.expectJsonRequest(
                    requests, 'PATCH', view.model.url, {'bio': BIO}
                );
                AjaxHelpers.respondWithNoContent(requests);
                expect(view.el).toHaveClass('mode-display');

                view.$('.wrapper-u-field').click();
                view.$(valueInputSelector).val('').focusout();
                AjaxHelpers.respondWithNoContent(requests);
                expect(view.el).toHaveClass('mode-placeholder');
                expect(view.$('.u-field-value .u-field-value-readonly').text()).toBe(fieldData.placeholderValue);
            });

            it("correctly renders LinkFieldView", function() {
                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.LinkFieldView, {
                    title: 'Title',
                    linkTitle: 'Link title',
                    helpMessage: 'Click the link.',
                    valueAttribute: 'password-reset'
                });
                var view = new FieldViews.LinkFieldView(fieldData).render();

                FieldViewsSpecHelpers.expectTitleAndMessageToContain(view, fieldData.title, fieldData.helpMessage, false);
                expect(view.$('.u-field-value > a .u-field-link-title-' + view.options.valueAttribute).text().trim()).toBe(fieldData.linkTitle);
            });
        });
    });
