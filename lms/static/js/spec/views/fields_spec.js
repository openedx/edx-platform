define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/views/fields',
        'js/spec/views/fields_helpers',
        'string_utils'],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, FieldViews, FieldViewsSpecHelpers) {
        'use strict';

        var USERNAME = 'Legolas',
            FULLNAME = 'Legolas Thranduil',
            EMAIL = 'legolas@woodland.middlearth';

        describe("edx.FieldViews", function () {

            var requests,
                timerCallback;

            var fieldViewClasses = [
                FieldViews.ReadonlyFieldView,
                FieldViews.TextFieldView,
                FieldViews.DropdownFieldView,
                FieldViews.LinkFieldView,
            ];

            beforeEach(function () {
                TemplateHelpers.installTemplate('templates/fields/field_readonly');
                TemplateHelpers.installTemplate('templates/fields/field_dropdown');
                TemplateHelpers.installTemplate('templates/fields/field_link');
                TemplateHelpers.installTemplate('templates/fields/field_text');

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
                    })

                    var view = new fieldViewClass(fieldData).render();
                    FieldViewsSpecHelpers.verifySuccessMessageReset(view, fieldData, timerCallback);
                }
            });

            it("sends a PATCH request when saveAttributes is called", function() {

                requests = AjaxHelpers.requests(this);

                var fieldViewClass = FieldViews.FieldView;
                var fieldData = FieldViewsSpecHelpers.createFieldData(fieldViewClass, {
                    title: 'Preferred Language',
                    valueAttribute: 'language',
                    helpMessage: 'Your preferred language.'
                })

                var view = new fieldViewClass(fieldData);
                view.saveAttributes(
                    {'language': 'ur'},
                    {'headers': {'Priority': 'Urgent'}}
                );

                var request = requests[0];
                expect(request.method).toBe('PATCH');
                expect(request.requestHeaders['Content-Type']).toBe('application/merge-patch+json;charset=utf-8');
                expect(request.requestHeaders['Priority']).toBe('Urgent');
                expect(request.requestBody).toBe('{"language":"ur"}');
            });

            it("correctly renders and updates ReadonlyFieldView", function() {
                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.ReadonlyFieldView, {
                    title: 'Username',
                    valueAttribute: 'username',
                    helpMessage: 'The username that you use to sign in to edX.'
                });
                var view = new FieldViews.ReadonlyFieldView(fieldData).render();

                FieldViewsSpecHelpers.expectTitleAndMessageToBe(view, fieldData.title, fieldData.helpMessage);
                expect(view.$('.u-field-value input').val().trim()).toBe(USERNAME);

                view.model.set({'username': 'bookworm'});
                expect(view.$('.u-field-value input').val().trim()).toBe('bookworm');
            });

            it("correctly renders, updates and persists changes to TextFieldView", function() {

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
                    validationError: "Think again!"
                }, requests);
            });

            it("correctly renders, updates and persists changes to DropdownFieldView", function() {

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
                    validationError: "Nope, this will not do!"
                }, requests);
            });

            it("correctly renders LinkFieldView", function() {
                var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.LinkFieldView, {
                    title: 'Title',
                    linkTitle: 'Link title',
                    helpMessage: 'Click the link.'
                });
                var view = new FieldViews.LinkFieldView(fieldData).render();

                FieldViewsSpecHelpers.expectTitleAndMessageToBe(view, fieldData.title, fieldData.helpMessage);
                expect(view.$('.u-field-value > a').text().trim()).toBe(fieldData.linkTitle);
            });
        });

    });
