(function() {
    'use strict';

    describe('XBlock', function() {
        beforeEach(function() {
            return setFixtures(
                '<div>\n' +
                '  <div class="xblock"\n' +
                '       id="vA"\n' +
                '       data-runtime-version="A"\n' +
                '       data-runtime-class="TestRuntime"\n' +
                '       data-init="initFnA"\n' +
                '       data-name="a-name"\n' +
                '  />\n' +
                '  <div>\n' +
                '    <div class="xblock"\n' +
                '         id="vZ"\n' +
                '         data-runtime-version="Z"\n' +
                '         data-runtime-class="TestRuntime"\n' +
                '         data-init="initFnZ"\n' +
                '         data-request-token="req-token-z"\n' +
                '    />\n' +
                '  </div>\n' +
                '  <div class="xblock" id="missing-version" data-init="initFnA" data-name="no-version"/>\n' +
                '  <div class="xblock" id="missing-init" data-runtime-version="A" data-name="no-init"/>\n' +
                '</div>');
        });
        describe('initializeBlock', function() {
            beforeEach(function() {
                window.TestRuntime = {};
                this.runtimeA = {
                    name: 'runtimeA'
                };
                this.runtimeZ = {
                    name: 'runtimeZ'
                };
                window.TestRuntime.vA = jasmine.createSpy().and.returnValue(this.runtimeA);
                window.TestRuntime.vZ = jasmine.createSpy().and.returnValue(this.runtimeZ);
                window.initFnA = jasmine.createSpy();
                window.initFnZ = jasmine.createSpy();
                this.fakeChildren = ['list', 'of', 'children'];
                spyOn(XBlock, 'initializeXBlocks').and.returnValue(this.fakeChildren);
                this.vANode = $('#vA')[0];
                this.vZNode = $('#vZ')[0];
                this.vABlock = XBlock.initializeBlock(this.vANode, 'req-token-a');
                this.vZBlock = XBlock.initializeBlock(this.vZNode);
                this.missingVersionBlock = XBlock.initializeBlock($('#missing-version')[0]);
                this.missingInitBlock = XBlock.initializeBlock($('#missing-init')[0]);
            });

            it('loads the right runtime version', function() {
                expect(window.TestRuntime.vA).toHaveBeenCalledWith();
                expect(window.TestRuntime.vZ).toHaveBeenCalledWith();
            });

            it('loads the right init function', function() {
                expect(window.initFnA).toHaveBeenCalledWith(this.runtimeA, this.vANode, {});
                expect(window.initFnZ).toHaveBeenCalledWith(this.runtimeZ, this.vZNode, {});
            });

            it('loads when missing versions', function() {
                expect(this.missingVersionBlock.element).toBe($('#missing-version')[0]);
                expect(this.missingVersionBlock.name).toBe('no-version');
            });

            it('loads when missing init fn', function() {
                expect(this.missingInitBlock.element).toBe($('#missing-init')[0]);
                expect(this.missingInitBlock.name).toBe('no-init');
            });

            it('adds names to blocks', function() {
                expect(this.vABlock.name).toBe('a-name');
            });

            it('leaves leaves missing names undefined', function() {
                expect(this.vZBlock.name).toBeUndefined();
            });

            it('attaches the element to the block', function() {
                expect(this.vABlock.element).toBe(this.vANode);
                expect(this.vZBlock.element).toBe(this.vZNode);
                expect(this.missingVersionBlock.element).toBe($('#missing-version')[0]);
                expect(this.missingInitBlock.element).toBe($('#missing-init')[0]);
            });

            it('passes through the request token', function() {
                expect(XBlock.initializeXBlocks).toHaveBeenCalledWith($(this.vANode), 'req-token-a');
                expect(XBlock.initializeXBlocks).toHaveBeenCalledWith($(this.vZNode), 'req-token-z');
            });
        });
        describe('initializeBlocks', function() {
            beforeEach(function() {
                spyOn(XBlock, 'initializeBlock');
                this.vANode = $('#vA')[0];
                this.vZNode = $('#vZ')[0];
            });

            it('initializes children', function() {
                XBlock.initializeBlocks($('#jasmine-fixtures'));
                expect(XBlock.initializeBlock).toHaveBeenCalledWith(this.vANode, void 0);
                expect(XBlock.initializeBlock).toHaveBeenCalledWith(this.vZNode, void 0);
            });

            it('only initializes matching request tokens', function() {
                XBlock.initializeBlocks($('#jasmine-fixtures'), 'req-token-z');
                expect(XBlock.initializeBlock).not.toHaveBeenCalledWith(this.vANode, jasmine.any(Object));
                expect(XBlock.initializeBlock).toHaveBeenCalledWith(this.vZNode, 'req-token-z');
            });
        });
        describe("renderXBlockFragment", function() {
            var postXBlockRequest;
            postXBlockRequest = function(resources) {
                var element, fragment, mock_xblock_html;
                mock_xblock_html = '<div class="mock_xblock"></div>';
                element = $('#vA');
                fragment = {
                    html: mock_xblock_html,
                    resources: resources
                };
              XBlock.renderXBlockFragment(fragment, element);
              expect(element.html()).toContain(mock_xblock_html);
            };

            it("can render an xblock with no CSS or JavaScript", function() {
                postXBlockRequest([]);
            });

            it("can render an xblock with required CSS", function() {
                var headHtml, mockCssText, mockCssUrl;
                mockCssText = "// Just a comment";
                mockCssUrl = "mock.css";
                postXBlockRequest([
                  [
                    "hash1", {
                      mimetype: "text/css",
                      kind: "text",
                      data: mockCssText
                    }
                  ], [
                    "hash2", {
                      mimetype: "text/css",
                      kind: "url",
                      data: mockCssUrl
                    }
                  ]
                ]);
                headHtml = $('head').html();
                expect(headHtml).toContain(mockCssText);
                expect(headHtml).toContain(mockCssUrl);
            });

            it("can render an xblock with required JavaScript", function() {
                postXBlockRequest([
                  [
                    "hash3", {
                      mimetype: "application/javascript",
                      kind: "text",
                      data: "window.test = 100;"
                    }
                  ]
                ]);
                expect(window.test).toBe(100);
            });

            it("can render an xblock with required HTML", function() {
                var mockHeadTag;
                mockHeadTag = "<title>Test Title</title>";
                postXBlockRequest([
                  [
                    "hash4", {
                      mimetype: "text/html",
                      placement: "head",
                      data: mockHeadTag
                    }
                  ]
                ]);
                expect($('head').html()).toContain(mockHeadTag);
            });
        });
    });
}).call(this);
