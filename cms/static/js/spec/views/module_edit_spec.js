(function() {
    'use strict';
    define([
        'jquery', 'common/js/components/utils/view_utils', 'js/spec_helpers/edit_helpers',
        'js/views/module_edit', 'js/models/module_info', 'xmodule'],
    function($, ViewUtils, edit_helpers, ModuleEdit, ModuleModel) {
        describe('ModuleEdit', function() {
            beforeEach(function() {
                this.stubModule = new ModuleModel({
                    id: 'stub-id'
                });
                setFixtures('<ul>\n' +
                            '<li class="component" id="stub-id" data-locator="stub-id">\n' +
                            '  <div class="component-editor">\n' +
                            '    <div class="module-editor">\n' +
                            '      ${editor}\n' +
                            '    </div>\n' +
                            '    <a href="#" class="save-button">Save</a>\n' +
                            '    <a href="#" class="cancel-button">Cancel</a>\n' +
                            '  </div>\n' +
                            '  <div class="component-actions">\n' +
                            '    <a href="#" class="edit-button"><span class="edit-icon white"></span>Edit</a>\n' +
                            '    <a href="#" class="delete-button"><span class="delete-icon white">' +
                                '</span>Delete</a>\n' +
                            '  </div>\n' +
                            '  <span class="drag-handle action"></span>\n' +
                            '  <section class="xblock xblock-student_view xmodule_display xmodule_stub"' +
                                ' data-type="StubModule">\n' +
                            '    <div id="stub-module-content"/>\n' +
                            '  </section>\n' +
                            '</li>\n' +
                            '</ul>');
                edit_helpers.installEditTemplates(true);
                spyOn($, 'ajax').and.returnValue(this.moduleData);
                this.moduleEdit = new ModuleEdit({
                    el: $('.component'),
                    model: this.stubModule,
                    onDelete: jasmine.createSpy()
                });
                return this.moduleEdit;
            });
            describe('class definition', function() {
                it('sets the correct tagName', function() {
                    return expect(this.moduleEdit.tagName).toEqual('li');
                });
                it('sets the correct className', function() {
                    return expect(this.moduleEdit.className).toEqual('component');
                });
            });
            describe('methods', function() {
                describe('initialize', function() {
                    beforeEach(function() {
                        spyOn(ModuleEdit.prototype, 'render');
                        this.moduleEdit = new ModuleEdit({
                            el: $('.component'),
                            model: this.stubModule,
                            onDelete: jasmine.createSpy()
                        });
                        return this.moduleEdit;
                    });
                    it('renders the module editor', function() {
                        return expect(ModuleEdit.prototype.render).toHaveBeenCalled();
                    });
                });
                describe('render', function() {
                    beforeEach(function() {
                        spyOn(this.moduleEdit, 'loadDisplay');
                        spyOn(this.moduleEdit, 'delegateEvents');
                        spyOn($.fn, 'append');
                        spyOn(ViewUtils, 'loadJavaScript').and.returnValue($.Deferred().resolve().promise());
                        window.MockXBlock = function() {
                            return {};
                        };
                        window.loadedXBlockResources = void 0;
                        this.moduleEdit.render();
                        return $.ajax.calls.mostRecent().args[0].success({
                            html: '<div>Response html</div>',
                            resources: [
                                [
                                    'hash1', {
                                        kind: 'text',
                                        mimetype: 'text/css',
                                        data: 'inline-css'
                                    }
                                ], [
                                    'hash2', {
                                        kind: 'url',
                                        mimetype: 'text/css',
                                        data: 'css-url'
                                    }
                                ], [
                                    'hash3', {
                                        kind: 'text',
                                        mimetype: 'application/javascript',
                                        data: 'inline-js'
                                    }
                                ], [
                                    'hash4', {
                                        kind: 'url',
                                        mimetype: 'application/javascript',
                                        data: 'js-url'
                                    }
                                ], [
                                    'hash5', {
                                        placement: 'head',
                                        mimetype: 'text/html',
                                        data: 'head-html'
                                    }
                                ], [
                                    'hash6', {
                                        placement: 'not-head',
                                        mimetype: 'text/html',
                                        data: 'not-head-html'
                                    }
                                ]
                            ]
                        });
                    });
                    afterEach(function() {
                        window.MockXBlock = null;
                        return window.MockXBlock;
                    });
                    it('loads the module preview via ajax on the view element', function() {
                        expect($.ajax).toHaveBeenCalledWith({
                            url: '/xblock/' + this.moduleEdit.model.id + '/student_view',
                            type: 'GET',
                            cache: false,
                            headers: {
                                Accept: 'application/json'
                            },
                            success: jasmine.any(Function)
                        });
                        expect($.ajax).not.toHaveBeenCalledWith({
                            url: '/xblock/' + this.moduleEdit.model.id + '/studio_view',
                            type: 'GET',
                            headers: {
                                Accept: 'application/json'
                            },
                            success: jasmine.any(Function)
                        });
                        expect(this.moduleEdit.loadDisplay).toHaveBeenCalled();
                        return expect(this.moduleEdit.delegateEvents).toHaveBeenCalled();
                    });
                    it('loads the editing view via ajax on demand', function() {
                        var mockXBlockEditorHtml;
                        edit_helpers.installEditTemplates(true);
                        expect($.ajax).not.toHaveBeenCalledWith({
                            url: '/xblock/' + this.moduleEdit.model.id + '/studio_view',
                            type: 'GET',
                            cache: false,
                            headers: {
                                Accept: 'application/json'
                            },
                            success: jasmine.any(Function)
                        });
                        this.moduleEdit.clickEditButton({
                            'preventDefault': jasmine.createSpy('event.preventDefault')
                        });
                        mockXBlockEditorHtml = readFixtures('mock/mock-xblock-editor.underscore');
                        $.ajax.calls.mostRecent().args[0].success({
                            html: mockXBlockEditorHtml,
                            resources: [
                                [
                                    'hash1', {
                                        kind: 'text',
                                        mimetype: 'text/css',
                                        data: 'inline-css'
                                    }
                                ], [
                                    'hash2', {
                                        kind: 'url',
                                        mimetype: 'text/css',
                                        data: 'css-url'
                                    }
                                ], [
                                    'hash3', {
                                        kind: 'text',
                                        mimetype: 'application/javascript',
                                        data: 'inline-js'
                                    }
                                ], [
                                    'hash4', {
                                        kind: 'url',
                                        mimetype: 'application/javascript',
                                        data: 'js-url'
                                    }
                                ], [
                                    'hash5', {
                                        placement: 'head',
                                        mimetype: 'text/html',
                                        data: 'head-html'
                                    }
                                ], [
                                    'hash6', {
                                        placement: 'not-head',
                                        mimetype: 'text/html',
                                        data: 'not-head-html'
                                    }
                                ]
                            ]
                        });
                        expect($.ajax).toHaveBeenCalledWith({
                            url: '/xblock/' + this.moduleEdit.model.id + '/studio_view',
                            type: 'GET',
                            cache: false,
                            headers: {
                                Accept: 'application/json'
                            },
                            success: jasmine.any(Function)
                        });
                        return expect(this.moduleEdit.delegateEvents).toHaveBeenCalled();
                    });
                    it('loads inline css from fragments', function() {
                        var args = "<style type='text/css'>inline-css</style>";
                        return expect($('head').append).toHaveBeenCalledWith(args);
                    });
                    it('loads css urls from fragments', function() {
                        var args = "<link rel='stylesheet' href='css-url' type='text/css'>";
                        return expect($('head').append).toHaveBeenCalledWith(args);
                    });
                    it('loads inline js from fragments', function() {
                        return expect($('head').append).toHaveBeenCalledWith('<script>inline-js</script>');
                    });
                    it('loads js urls from fragments', function() {
                        return expect(ViewUtils.loadJavaScript).toHaveBeenCalledWith('js-url');
                    });
                    it('loads head html', function() {
                        return expect($('head').append).toHaveBeenCalledWith('head-html');
                    });
                    it("doesn't load body html", function() {
                        return expect($.fn.append).not.toHaveBeenCalledWith("not-head-html");
                    });
                    it("doesn't reload resources", function() {
                        var count;
                        count = $('head').append.calls.count();
                        $.ajax.calls.mostRecent().args[0].success({
                            html: '<div>Response html 2</div>',
                            resources: [
                                [
                                    'hash1', {
                                        kind: 'text',
                                        mimetype: 'text/css',
                                        data: 'inline-css'
                                    }
                                ]
                            ]
                        });
                        return expect($('head').append.calls.count()).toBe(count);
                    });
                });
                describe('loadDisplay', function() {
                    beforeEach(function() {
                        spyOn(XBlock, 'initializeBlock');
                        return this.moduleEdit.loadDisplay();
                    });
                    it('loads the .xmodule-display inside the module editor', function() {
                        expect(XBlock.initializeBlock).toHaveBeenCalled();
                        var sel = '.xblock-student_view';
                        return expect(XBlock.initializeBlock.calls.mostRecent().args[0].get(0)).toBe($(sel).get(0));
                    });
                });
            });
        });
    });
}).call(this);
