(function() {
	'use strict';

    /*global HTMLEditingDescriptor */
    describe('HTMLEditingDescriptor', function() {
        beforeEach(function() {
            window.baseUrl = "/static/deadbeef";
            return window.baseUrl;
        });
        afterEach(function() {
            return delete window.baseUrl;
        });
        describe('Visual HTML Editor', function() {
            beforeEach(function() {
                loadFixtures('html-edit-visual.html');
                this.descriptor = new HTMLEditingDescriptor($('.test-component'));
                return this.descriptor;
            });
            it('Returns data from Visual Editor if text has changed', function() {
                var data, visualEditorStub;
                visualEditorStub = {
                    getContent: function() {
                        return 'from visual editor';
                    }
                };
                spyOn(this.descriptor, 'getVisualEditor').and.callFake(function() {
                    return visualEditorStub;
                });
                data = this.descriptor.save().data;
                return expect(data).toEqual('from visual editor');
            });
            it('Returns data from Raw Editor if text has not changed', function() {
                var data, visualEditorStub;
                visualEditorStub = {
                    getContent: function() {
                        return '<p>original visual text</p>';
                    }
                };
                spyOn(this.descriptor, 'getVisualEditor').and.callFake(function() {
                    return visualEditorStub;
                });
                data = this.descriptor.save().data;
                return expect(data).toEqual('raw text');
            });
            it('Performs link rewriting for static assets when saving', function() {
                var data, visualEditorStub;
                visualEditorStub = {
                    getContent: function() {
                        return 'from visual editor with /c4x/foo/bar/asset/image.jpg';
                    }
                };
                spyOn(this.descriptor, 'getVisualEditor').and.callFake(function() {
                    return visualEditorStub;
                });
                data = this.descriptor.save().data;
                return expect(data).toEqual('from visual editor with /static/image.jpg');
            });
            it('When showing visual editor links are rewritten to c4x format', function() {
                var visualEditorStub;
                visualEditorStub = {
                    content: 'text /static/image.jpg',
                    startContent: 'text /static/image.jpg',
                    focus: function() {},
                    setContent: function(x) {
                        this.content = x;
                        return this.content;
                    },
                    getContent: function() {
                        return this.content;
                    }
                };
                this.descriptor.initInstanceCallback(visualEditorStub);
                return expect(visualEditorStub.getContent()).toEqual('text /c4x/foo/bar/asset/image.jpg');
            });
            return it('Enables spellcheck', function() {
                return expect($('.html-editor iframe')[0].contentDocument.body.spellcheck).toBe(true);
            });
        });
        return describe('Raw HTML Editor', function() {
            beforeEach(function() {
                loadFixtures('html-editor-raw.html');
                this.descriptor = new HTMLEditingDescriptor($('.test-component'));
                return this.descriptor;
            });
            return it('Returns data from raw editor', function() {
                var data;
                data = this.descriptor.save().data;
                return expect(data).toEqual('raw text');
            });
        });
    });

}).call(this);
