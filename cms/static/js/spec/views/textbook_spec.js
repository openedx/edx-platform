(function(sandbox, CMS) {
    'use strict';
    define(['js/models/textbook', 'js/models/chapter', 'js/collections/chapter', 'js/models/course',
            'js/collections/textbook', 'js/views/show_textbook', 'js/views/edit_textbook', 'js/views/list_textbooks',
            'js/views/edit_chapter', 'common/js/components/views/feedback_prompt',
            'common/js/components/views/feedback_notification', 'common/js/components/utils/view_utils',
            'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers', 'js/spec_helpers/modal_helpers'],
            function(Textbook, Chapter, ChapterSet, Course, TextbookSet, ShowTextbook, EditTextbook,
                     ListTextbooks, EditChapter, Prompt, Notification, ViewUtils, AjaxHelpers, modal_helpers) {
        describe('ShowTextbook', function() {
            var tpl;
            tpl = readFixtures('show-textbook.underscore');
            beforeEach(function() {
                setFixtures($('<script>', {
                    id: 'show-textbook-tpl',
                    type: 'text/template'
                }).text(tpl));
                appendSetFixtures(sandbox({
                    id: 'page-notification'
                }));
                appendSetFixtures(sandbox({
                    id: 'page-prompt'
                }));
                this.model = new Textbook({
                    name: 'Life Sciences',
                    id: '0life-sciences'
                });
                spyOn(this.model, 'destroy').and.callThrough();
                this.collection = new TextbookSet([this.model]);
                this.view = new ShowTextbook({
                    model: this.model
                });
                this.promptSpies = jasmine.stealth.spyOnConstructor(Prompt, 'Warning', ['show', 'hide']);
                this.promptSpies.show.and.returnValue(this.promptSpies);
                window.course = new Course({
                    id: '5',
                    name: 'Course Name',
                    url_name: 'course_name',
                    org: 'course_org',
                    num: 'course_num',
                    revision: 'course_rev'
                });
            });
            afterEach(function() {
                delete window.course;
            });
            describe('Basic', function() {
                it('should render properly', function() {
                    this.view.render();
                    expect(this.view.$el).toContainText('Life Sciences');
                });
                it('should set the "editing" property on the model when the edit button is clicked', function() {
                    this.view.render().$('.edit').click();
                    expect(this.model.get('editing')).toBeTruthy();
                });
                it('should pop a delete confirmation when the delete button is clicked', function() {
                    var ctorOptions;
                    this.view.render().$('.delete').click();
                    expect(this.promptSpies.constructor).toHaveBeenCalled();
                    ctorOptions = this.promptSpies.constructor.calls.mostRecent().args[0];
                    expect(ctorOptions.title).toMatch(/Life Sciences/);
                    expect(this.model.destroy).not.toHaveBeenCalled();
                    expect(this.collection).toContain(this.model);
                });
                it('should show chapters appropriately', function() {
                    this.model.get('chapters').add([{}, {}, {}]);
                    this.model.set('showChapters', false);
                    this.view.render().$('.show-chapters').click();
                    expect(this.model.get('showChapters')).toBeTruthy();
                });
                it('should hide chapters appropriately', function() {
                    this.model.get('chapters').add([{}, {}, {}]);
                    this.model.set('showChapters', true);
                    this.view.render().$('.hide-chapters').click();
                    expect(this.model.get('showChapters')).toBeFalsy();
                });
            });
            describe('AJAX', function() {
                beforeEach(function() {
                    this.savingSpies = jasmine.stealth.spyOnConstructor(Notification, 'Mini', ['show', 'hide']);
                    this.savingSpies.show.and.returnValue(this.savingSpies);
                    CMS.URL.TEXTBOOKS = '/textbooks';
                });
                afterEach(function() {
                    delete CMS.URL.TEXTBOOKS;
                });
                it('should destroy itself on confirmation', function() {
                    var ctorOptions, requests, savingOptions;
                    requests = AjaxHelpers.requests(this);
                    this.view.render().$('.delete').click();
                    ctorOptions = this.promptSpies.constructor.calls.mostRecent().args[0];
                    ctorOptions.actions.primary.click(this.promptSpies);
                    expect(this.model.destroy).toHaveBeenCalled();
                    expect(requests.length).toEqual(1);
                    expect(this.savingSpies.constructor).toHaveBeenCalled();
                    expect(this.savingSpies.show).toHaveBeenCalled();
                    expect(this.savingSpies.hide).not.toHaveBeenCalled();
                    savingOptions = this.savingSpies.constructor.calls.mostRecent().args[0];
                    expect(savingOptions.title).toMatch(/Deleting/);
                    requests[0].respond(204);
                    expect(this.savingSpies.hide).toHaveBeenCalled();
                    expect(this.collection.contains(this.model)).toBeFalsy();
                });
            });
        });
        describe('EditTextbook', function() {
            describe('Basic', function() {
                var tpl;
                tpl = readFixtures('edit-textbook.underscore');
                beforeEach(function() {
                    setFixtures($('<script>', {
                        id: 'edit-textbook-tpl',
                        type: 'text/template'
                    }).text(tpl));
                    appendSetFixtures(sandbox({
                        id: 'page-notification'
                    }));
                    appendSetFixtures(sandbox({
                        id: 'page-prompt'
                    }));
                    this.model = new Textbook({
                        name: 'Life Sciences',
                        editing: true
                    });
                    spyOn(this.model, 'save');
                    this.collection = new TextbookSet();
                    this.collection.add(this.model);
                    this.view = new EditTextbook({
                        model: this.model
                    });
                    spyOn(this.view, 'render').and.callThrough();
                });
                it('should render properly', function() {
                    this.view.render();
                    expect(this.view.$('input[name=textbook-name]').val()).toEqual('Life Sciences');
                });
                it('should allow you to create new empty chapters', function() {
                    var numChapters;
                    this.view.render();
                    numChapters = this.model.get('chapters').length;
                    this.view.$('.action-add-chapter').click();
                    expect(this.model.get('chapters').length).toEqual(numChapters + 1);
                    expect(this.model.get('chapters').last().isEmpty()).toBeTruthy();
                });
                it('should save properly', function() {
                    var chapter;
                    this.view.render();
                    this.view.$('input[name=textbook-name]').val('starfish');
                    this.view.$('input[name=chapter1-name]').val('wallflower');
                    this.view.$('input[name=chapter1-asset-path]').val('foobar');
                    this.view.$('form').submit();
                    expect(this.model.get('name')).toEqual('starfish');
                    chapter = this.model.get('chapters').first();
                    expect(chapter.get('name')).toEqual('wallflower');
                    expect(chapter.get('asset_path')).toEqual('foobar');
                    expect(this.model.save).toHaveBeenCalled();
                });
                it('should not save on invalid', function() {
                    this.view.render();
                    this.view.$('input[name=textbook-name]').val('');
                    this.view.$('input[name=chapter1-asset-path]').val('foobar.pdf');
                    this.view.$('form').submit();
                    expect(this.model.validationError).toBeTruthy();
                    expect(this.model.save).not.toHaveBeenCalled();
                });
                it('does not save on cancel', function() {
                    var chapter;
                    this.model.get('chapters').add([
                        {
                            name: 'a',
                            asset_path: 'b'
                        }
                    ]);
                    this.view.render();
                    this.view.$('input[name=textbook-name]').val('starfish');
                    this.view.$('input[name=chapter1-asset-path]').val('foobar.pdf');
                    this.view.$('.action-cancel').click();
                    expect(this.model.get('name')).not.toEqual('starfish');
                    chapter = this.model.get('chapters').first();
                    expect(chapter.get('asset_path')).not.toEqual('foobar');
                    expect(this.model.save).not.toHaveBeenCalled();
                });
                it('should be possible to correct validation errors', function() {
                    this.view.render();
                    this.view.$('input[name=textbook-name]').val('');
                    this.view.$('input[name=chapter1-asset-path]').val('foobar.pdf');
                    this.view.$('form').submit();
                    expect(this.model.validationError).toBeTruthy();
                    expect(this.model.save).not.toHaveBeenCalled();
                    this.view.$('input[name=textbook-name]').val('starfish');
                    this.view.$('input[name=chapter1-name]').val('foobar');
                    this.view.$('form').submit();
                    expect(this.model.validationError).toBeFalsy();
                    expect(this.model.save).toHaveBeenCalled();
                });
                it('removes all empty chapters on cancel if the model has a non-empty chapter', function() {
                    var chapters;
                    chapters = this.model.get('chapters');
                    chapters.at(0).set('name', 'non-empty');
                    this.model.setOriginalAttributes();
                    this.view.render();
                    chapters.add([{}, {}, {}]);
                    expect(chapters.length).toEqual(4);
                    this.view.$('.action-cancel').click();
                    expect(chapters.length).toEqual(1);
                    expect(chapters.first().get('name')).toEqual('non-empty');
                });
                it('removes all empty chapters on cancel except one if the model has no non-empty chapters',
                    function() {
                    var chapters;
                    chapters = this.model.get('chapters');
                    this.view.render();
                    chapters.add([{}, {}, {}]);
                    expect(chapters.length).toEqual(4);
                    this.view.$('.action-cancel').click();
                    expect(chapters.length).toEqual(1);
                });
            });
        });
        describe('ListTextbooks', function() {
            var editTextbooktpl, noTextbooksTpl;
            noTextbooksTpl = readFixtures('no-textbooks.underscore');
            editTextbooktpl = readFixtures('edit-textbook.underscore');
            beforeEach(function() {
                appendSetFixtures($('<script>', {
                    id: 'no-textbooks-tpl',
                    type: 'text/template'
                }).text(noTextbooksTpl));
                appendSetFixtures($('<script>', {
                    id: 'edit-textbook-tpl',
                    type: 'text/template'
                }).text(editTextbooktpl));
                this.collection = new TextbookSet();
                this.view = new ListTextbooks({
                    collection: this.collection
                });
                this.view.render();
            });
            it('should scroll to newly added textbook', function() {
                var $sectionEl;
                spyOn(ViewUtils, 'setScrollOffset');
                this.view.$('.new-button').click();
                $sectionEl = this.view.$el.find('section:last');
                expect($sectionEl.length).toEqual(1);
                expect(ViewUtils.setScrollOffset).toHaveBeenCalledWith($sectionEl, 0);
            });
            it('should focus first input element of newly added textbook', function() {
                var $inputEl;
                spyOn(jQuery.fn, 'focus').and.callThrough();
                jasmine.addMatchers({
                    toHaveBeenCalledOnJQueryObject: function() {
                        return {
                            compare: function(actual, expected) {
                                var condition = actual.calls.mostRecent().object[0] === expected[0];
                                return {
                                    pass: actual.calls && actual.calls.mostRecent() && condition
                                };
                            }
                        };
                    }
                });
                this.view.$('.new-button').click();
                $inputEl = this.view.$el.find('section:last input:first');
                expect($inputEl.length).toEqual(1);
                expect(jQuery.fn.focus).toHaveBeenCalledOnJQueryObject($inputEl);
            });
        });
        describe('EditChapter', function() {
            beforeEach(function() {
                modal_helpers.installModalTemplates();
                this.model = new Chapter({
                    name: 'Chapter 1',
                    asset_path: '/ch1.pdf'
                });
                this.collection = new ChapterSet();
                this.collection.add(this.model);
                this.view = new EditChapter({
                    model: this.model
                });
                spyOn(this.view, 'remove').and.callThrough();
                CMS.URL.UPLOAD_ASSET = '/upload';
                window.course = new Course({
                    name: 'abcde'
                });
            });
            afterEach(function() {
                delete CMS.URL.UPLOAD_ASSET;
                delete window.course;
            });
            it('can render', function() {
                this.view.render();
                expect(this.view.$('input.chapter-name').val()).toEqual('Chapter 1');
                expect(this.view.$('input.chapter-asset-path').val()).toEqual('/ch1.pdf');
            });
            it('can delete itself', function() {
                this.view.render().$('.action-close').click();
                expect(this.collection.length).toEqual(0);
                expect(this.view.remove).toHaveBeenCalled();
            });
            xit('saves content when opening upload dialog', function() {
                this.view.render();
                this.view.$('input.chapter-name').val('rainbows');
                this.view.$('input.chapter-asset-path').val('unicorns');
                this.view.$('.action-upload').click();
                expect(this.model.get('name')).toEqual('rainbows');
                expect(this.model.get('asset_path')).toEqual('unicorns');
            });
        });
    });

}).call(this, sandbox, CMS);  //jshint ignore:line
