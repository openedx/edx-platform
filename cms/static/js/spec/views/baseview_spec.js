// eslint-disable-next-line no-undef
define(['jquery', 'underscore', 'js/views/baseview', 'js/utils/handle_iframe_binding', 'sinon'],
    function($, _, BaseView, IframeBinding, sinon) {
        describe('BaseView', function() {
            var baseViewPrototype;

            describe('BaseView rendering', function() {
                // eslint-disable-next-line camelcase
                var iframeBinding_spy;

                beforeEach(function() {
                    baseViewPrototype = BaseView.prototype;
                    // eslint-disable-next-line camelcase
                    iframeBinding_spy = sinon.spy(IframeBinding, 'iframeBinding');

                    // eslint-disable-next-line no-undef
                    spyOn(baseViewPrototype, 'initialize');
                    // eslint-disable-next-line no-undef
                    spyOn(baseViewPrototype, 'beforeRender');
                    // eslint-disable-next-line no-undef
                    spyOn(baseViewPrototype, 'render').and.callThrough();
                    // eslint-disable-next-line no-undef
                    spyOn(baseViewPrototype, 'afterRender').and.callThrough();
                });

                afterEach(function() {
                    // eslint-disable-next-line camelcase
                    iframeBinding_spy.restore();
                });

                it('calls before and after render functions when render of baseview is called', function() {
                    var baseView = new BaseView();
                    baseView.render();

                    expect(baseViewPrototype.initialize).toHaveBeenCalled();
                    expect(baseViewPrototype.beforeRender).toHaveBeenCalled();
                    expect(baseViewPrototype.render).toHaveBeenCalled();
                    expect(baseViewPrototype.afterRender).toHaveBeenCalled();
                });

                it('calls iframeBinding function when afterRender of baseview is called', function() {
                    var baseView = new BaseView();
                    baseView.render();
                    expect(baseViewPrototype.afterRender).toHaveBeenCalled();
                    // eslint-disable-next-line camelcase
                    expect(iframeBinding_spy.called).toEqual(true);

                    // check calls count of iframeBinding function
                    // eslint-disable-next-line camelcase
                    expect(iframeBinding_spy.callCount).toBe(1);
                    IframeBinding.iframeBinding();
                    // eslint-disable-next-line camelcase
                    expect(iframeBinding_spy.callCount).toBe(2);
                });
            });

            describe('Expand/Collapse', function() {
                var view, MockCollapsibleViewClass;

                MockCollapsibleViewClass = BaseView.extend({
                    initialize: function() {
                        this.viewHtml = readFixtures('mock/mock-collapsible-view.underscore');
                    },

                    render: function() {
                        this.$el.html(this.viewHtml);
                    }
                });

                it('hides a collapsible node when clicking on the toggle link', function() {
                    view = new MockCollapsibleViewClass();
                    view.render();
                    view.$('.ui-toggle-expansion').click();
                    expect(view.$('.expand-collapse')).toHaveClass('expand');
                    expect(view.$('.expand-collapse')).not.toHaveClass('collapse');
                    expect(view.$('.is-collapsible')).toHaveClass('collapsed');
                });

                it('expands a collapsible node when clicking twice on the toggle link', function() {
                    view = new MockCollapsibleViewClass();
                    view.render();
                    view.$('.ui-toggle-expansion').click();
                    view.$('.ui-toggle-expansion').click();
                    expect(view.$('.expand-collapse')).toHaveClass('collapse');
                    expect(view.$('.expand-collapse')).not.toHaveClass('expand');
                    expect(view.$('.is-collapsible')).not.toHaveClass('collapsed');
                });
            });
        });
    });
