(function() {
    'use strict';
    define(['js/views/course_info_handout', 'js/views/course_info_update', 'js/models/module_info',
            'js/collections/course_update', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'],
            function(CourseInfoHandoutsView, CourseInfoUpdateView, ModuleInfo, CourseUpdateCollection, AjaxHelpers) {
        describe('Course Updates and Handouts', function() {
            var courseInfoPage;
            courseInfoPage = '<div class="course-info-wrapper">\n' +
                             '<div class="main-column window">\n' +
                             '<article class="course-updates" id="course-update-view">\n' +
                             '<ol class="update-list" id="course-update-list"></ol>\n' +
                             '</article>\n' +
                             '</div>\n' +
                             '<div class="sidebar window course-handouts" id="course-handouts-view"></div>\n' +
                             '</div>\n' +
                             '<div class="modal-cover"></div>';
            beforeEach(function() {
                window.analytics = jasmine.createSpyObj('analytics', ['track']);
                window.course_location_analytics = jasmine.createSpy();
                return window.course_location_analytics;
            });
            afterEach(function() {
                delete window.analytics;
                return delete window.course_location_analytics;
            });
            describe('Course Updates without Push notification', function() {
                var courseInfoTemplate;
                courseInfoTemplate = readFixtures('course_info_update.underscore');
                beforeEach(function() {
                    var cancelEditingUpdate;
                    setFixtures($('<script>', {
                        id: 'course_info_update-tpl',
                        type: 'text/template'
                    }).text(courseInfoTemplate));
                    appendSetFixtures(courseInfoPage);
                    this.collection = new CourseUpdateCollection();
                    this.collection.url = 'course_info_update/';
                    this.courseInfoEdit = new CourseInfoUpdateView({
                        el: $('.course-updates'),
                        collection: this.collection,
                        base_asset_url: 'base-asset-url/'
                    });
                    this.courseInfoEdit.render();
                    this.event = {
                        preventDefault: function() {
                            return 'no op';
                        }
                    };
                    this.createNewUpdate = function(text) {
                        this.courseInfoEdit.onNew(this.event);
                        spyOn(this.courseInfoEdit.$codeMirror, 'getValue').and.returnValue(text);
                        return this.courseInfoEdit.$el.find('.save-button').click();
                    };
                    this.cancelNewCourseInfo = function(useCancelButton) {
                        var model, previewContents;
                        this.courseInfoEdit.onNew(this.event);
                        spyOn(this.courseInfoEdit.$modalCover, 'hide').and.callThrough();
                        spyOn(this.courseInfoEdit.$codeMirror, 'getValue').and.returnValue('unsaved changes');
                        model = this.collection.at(0);
                        spyOn(model, 'save').and.callThrough();
                        cancelEditingUpdate(this.courseInfoEdit, this.courseInfoEdit.$modalCover, useCancelButton);
                        expect(this.courseInfoEdit.$modalCover.hide).toHaveBeenCalled();
                        expect(model.save).not.toHaveBeenCalled();
                        previewContents = this.courseInfoEdit.$el.find('.update-contents').html();
                        expect(previewContents).not.toEqual('unsaved changes');
                    };
                    this.doNotCloseNewCourseInfo = function() {
                        var model;
                        this.courseInfoEdit.onNew(this.event);
                        spyOn(this.courseInfoEdit.$modalCover, 'hide').and.callThrough();
                        spyOn(this.courseInfoEdit.$codeMirror, 'getValue').and.returnValue('unsaved changes');
                        model = this.collection.at(0);
                        spyOn(model, 'save').and.callThrough();
                        cancelEditingUpdate(this.courseInfoEdit, this.courseInfoEdit.$modalCover, false);
                        expect(model.save).not.toHaveBeenCalled();
                        expect(this.courseInfoEdit.$modalCover.hide).not.toHaveBeenCalled();
                    };
                    this.cancelExistingCourseInfo = function(useCancelButton) {
                        var model, previewContents;
                        this.createNewUpdate('existing update');
                        this.courseInfoEdit.$el.find('.edit-button').click();
                        spyOn(this.courseInfoEdit.$modalCover, 'hide').and.callThrough();
                        spyOn(this.courseInfoEdit.$codeMirror, 'getValue').and.returnValue('modification');
                        model = this.collection.at(0);
                        spyOn(model, 'save').and.callThrough();
                        model.id = 'saved_to_server';
                        cancelEditingUpdate(this.courseInfoEdit, this.courseInfoEdit.$modalCover, useCancelButton);
                        expect(this.courseInfoEdit.$modalCover.hide).toHaveBeenCalled();
                        expect(model.save).not.toHaveBeenCalled();
                        previewContents = this.courseInfoEdit.$el.find('.update-contents').html();
                        expect(previewContents).toEqual('existing update');
                    };
                    this.testInvalidDateValue = function(value) {
                        this.courseInfoEdit.onNew(this.event);
                        expect(this.courseInfoEdit.$el.find('.save-button').hasClass('is-disabled')).toEqual(false);
                        this.courseInfoEdit.$el.find('input.date').val(value).trigger('change');
                        expect(this.courseInfoEdit.$el.find('.save-button').hasClass('is-disabled')).toEqual(true);
                        this.courseInfoEdit.$el.find('input.date').val('01/01/16').trigger('change');
                        expect(this.courseInfoEdit.$el.find('.save-button').hasClass('is-disabled'))
                            .toEqual(false);
                    };
                    cancelEditingUpdate = function(update, modalCover, useCancelButton) {
                        if (useCancelButton) {
                            return update.$el.find('.cancel-button').click();
                        } else {
                            return modalCover.click();
                        }
                    };
                    return cancelEditingUpdate;
                });
                it('does send expected data on save', function() {
                    var model, requestSent, requests;
                    requests = AjaxHelpers.requests(this);
                    expect(this.collection.isEmpty()).toBeTruthy();
                    this.courseInfoEdit.onNew(this.event);
                    expect(this.collection.length).toEqual(1);
                    model = this.collection.at(0);
                    spyOn(model, 'save').and.callThrough();
                    spyOn(this.courseInfoEdit.$codeMirror, 'getValue').and.returnValue('/static/image.jpg');
                    this.courseInfoEdit.$el.find('.save-button').click();
                    expect(model.save).toHaveBeenCalled();
                    requestSent = JSON.parse(requests[requests.length - 1].requestBody);
                    expect(requestSent.push_notification_selected).toEqual(false);
                    expect(requestSent.content).toEqual('/static/image.jpg');
                    expect(window.analytics.track).toHaveBeenCalled();
                });
                it('does rewrite links for preview', function() {
                    var previewContents;
                    this.createNewUpdate('/static/image.jpg');
                    previewContents = this.courseInfoEdit.$el.find('.update-contents').html();
                    expect(previewContents).toEqual('base-asset-url/image.jpg');
                });
                it('shows static links in edit mode', function() {
                    this.createNewUpdate('/static/image.jpg');
                    this.courseInfoEdit.$el.find('.edit-button').click();
                    expect(this.courseInfoEdit.$codeMirror.getValue()).toEqual('/static/image.jpg');
                });
                it('removes newly created course info on cancel', function() {
                    return this.cancelNewCourseInfo(true);
                });
                it('do not close new course info on click outside modal', function() {
                    return this.doNotCloseNewCourseInfo();
                });
                it('does not remove existing course info on cancel', function() {
                    return this.cancelExistingCourseInfo(true);
                });
                it('does not remove existing course info on click outside modal', function() {
                    return this.cancelExistingCourseInfo(false);
                });
                it('does not allow updates to be saved with an invalid date', function() {
                    return this.testInvalidDateValue('Marchtober 40, 2048');
                });
                it('does not allow updates to be saved with a blank date', function() {
                    return this.testInvalidDateValue('');
                });
            });
            describe('Course Updates WITH Push notification', function() {
                var courseInfoTemplate;
                courseInfoTemplate = readFixtures('course_info_update.underscore');
                beforeEach(function() {
                    setFixtures($('<script>', {
                        id: 'course_info_update-tpl',
                        type: 'text/template'
                    }).text(courseInfoTemplate));
                    appendSetFixtures(courseInfoPage);
                    this.collection = new CourseUpdateCollection();
                    this.collection.url = 'course_info_update/';
                    this.courseInfoEdit = new CourseInfoUpdateView({
                        el: $('.course-updates'),
                        collection: this.collection,
                        base_asset_url: 'base-asset-url/',
                        push_notification_enabled: true
                    });
                    this.courseInfoEdit.render();
                    this.event = {
                        preventDefault: function() {
                            return 'no op';
                        }
                    };
                    return this.courseInfoEdit.onNew(this.event);
                });
                it('shows push notification checkbox as selected by default', function() {
                    expect(this.courseInfoEdit.$el.find('.toggle-checkbox')).toBeChecked();
                });
                it('sends correct default value for push_notification_selected', function() {
                    var analytics_payload, requestSent, requests;
                    requests = AjaxHelpers.requests(this);
                    this.courseInfoEdit.$el.find('.save-button').click();
                    requestSent = JSON.parse(requests[requests.length - 1].requestBody);
                    expect(requestSent.push_notification_selected).toEqual(true);
                    analytics_payload = window.analytics.track.calls.first().args[1];
                    expect(analytics_payload).toEqual(jasmine.objectContaining({
                        'push_notification_selected': true
                    }));
                });
                it('sends correct value for push_notification_selected when it is unselected', function() {
                    var analytics_payload, requestSent, requests;
                    requests = AjaxHelpers.requests(this);
                    this.courseInfoEdit.$el.find('.toggle-checkbox').attr('checked', false);
                    this.courseInfoEdit.$el.find('.save-button').click();
                    requestSent = JSON.parse(requests[requests.length - 1].requestBody);
                    expect(requestSent.push_notification_selected).toEqual(false);
                    analytics_payload = window.analytics.track.calls.first().args[1];
                    expect(analytics_payload).toEqual(jasmine.objectContaining({
                        'push_notification_selected': false
                    }));
                });
            });
            describe('Course Handouts', function() {
                var handoutsTemplate;
                handoutsTemplate = readFixtures('course_info_handouts.underscore');
                beforeEach(function() {
                    setFixtures($('<script>', {
                        id: 'course_info_handouts-tpl',
                        type: 'text/template'
                    }).text(handoutsTemplate));
                    appendSetFixtures(courseInfoPage);
                    this.model = new ModuleInfo({
                        id: 'handouts-id',
                        data: '/static/fromServer.jpg'
                    });
                    this.handoutsEdit = new CourseInfoHandoutsView({
                        el: $('#course-handouts-view'),
                        model: this.model,
                        base_asset_url: 'base-asset-url/'
                    });
                    return this.handoutsEdit.render();
                });
                it('does not rewrite links on save', function() {
                    var contentSaved, requests;
                    requests = AjaxHelpers.requests(this);
                    this.handoutsEdit.$el.find('.edit-button').click();
                    spyOn(this.handoutsEdit.$codeMirror, 'getValue').and.returnValue('/static/image.jpg');
                    spyOn(this.model, 'save').and.callThrough();
                    this.handoutsEdit.$el.find('.save-button').click();
                    expect(this.model.save).toHaveBeenCalled();
                    contentSaved = JSON.parse(requests[requests.length - 1].requestBody).data;
                    expect(contentSaved).toEqual('/static/image.jpg');
                });
                it('does rewrite links in initial content', function() {
                    expect(this.handoutsEdit.$preview.html().trim()).toBe('base-asset-url/fromServer.jpg');
                });
                it('does rewrite links after edit', function() {
                    this.handoutsEdit.$el.find('.edit-button').click();
                    spyOn(this.handoutsEdit.$codeMirror, 'getValue').and.returnValue('/static/image.jpg');
                    this.handoutsEdit.$el.find('.save-button').click();
                    expect(this.handoutsEdit.$preview.html().trim()).toBe('base-asset-url/image.jpg');
                });
                it('shows static links in edit mode', function() {
                    this.handoutsEdit.$el.find('.edit-button').click();
                    expect(this.handoutsEdit.$codeMirror.getValue().trim()).toEqual('/static/fromServer.jpg');
                });
                it('can open course handouts with bad html on edit', function() {
                    this.model = new ModuleInfo({
                        id: 'handouts-id',
                        data: '<p><a href="[URL OF FILE]>[LINK TEXT]</a></p>'
                    });
                    this.handoutsEdit = new CourseInfoHandoutsView({
                        el: $('#course-handouts-view'),
                        model: this.model,
                        base_asset_url: 'base-asset-url/'
                    });
                    this.handoutsEdit.render();
                    expect($('.edit-handouts-form').is(':hidden')).toEqual(true);
                    this.handoutsEdit.$el.find('.edit-button').click();
                    var result = '<p><a href="[URL OF FILE]>[LINK TEXT]</a></p>';
                    expect(this.handoutsEdit.$codeMirror.getValue()).toEqual(result);
                    expect($('.edit-handouts-form').is(':hidden')).toEqual(false);
                });
            });
        });
    });

}).call(this);
