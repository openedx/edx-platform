(function (define) {
    'use strict';

    define(['jquery',
            'underscore',
            'backbone',
            'js/components/tabbed/views/tabbed_view'
           ],
           function($, _, Backbone, TabbedView) {
               var view,
                   TestSubview = Backbone.View.extend({
                       initialize: function (options) {
                           this.text = options.text;
                       },

                       render: function () {
                           this.$el.text(this.text);
                       }
                   });

               describe('TabbedView component', function () {
                   beforeEach(function () {
                       spyOn(Backbone.history, 'navigate').andCallThrough();
                       Backbone.history.start();
                       view = new TabbedView({
                           tabs: [{
                               url: 'test 1',
                               title: 'Test 1',
                               view: new TestSubview({text: 'this is test text'})
                           }, {
                               url: 'test 2',
                               title: 'Test 2',
                               view: new TestSubview({text: 'other text'})
                           }]
                       });
                   });

                   afterEach(function () {
                       Backbone.history.stop();
                   });

                   it('can render itself', function () {
                       expect(view.$el.html()).toContain('<nav class="page-content-nav"');
                   });

                   it('shows its first tab by default', function () {
                       expect(view.$el.text()).toContain('this is test text');
                       expect(view.$el.text()).not.toContain('other text');
                   });

                   it('displays titles for each tab', function () {
                       expect(view.$el.text()).toContain('Test 1');
                       expect(view.$el.text()).toContain('Test 2');
                   });

                   it('can switch tabs', function () {
                       view.$('.nav-item[data-index=1]').click();
                       expect(view.$el.text()).not.toContain('this is test text');
                       expect(view.$el.text()).toContain('other text');
                   });

                   it('changes tabs on navigation', function () {
                       expect(view.$('.nav-item.is-active').data('index')).toEqual(0);
                       Backbone.history.navigate('test 2', {trigger: true});
                       expect(view.$('.nav-item.is-active').data('index')).toEqual(1);
                   });

                   it('marks the active tab as selected using aria attributes', function () {
                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr('aria-selected', 'true');
                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr('aria-selected', 'false');
                       view.$('.nav-item[data-index=1]').click();
                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr('aria-selected', 'false');
                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr('aria-selected', 'true');
                   });

                   it('updates the page URL on tab switches without adding to browser history', function () {
                       view.$('.nav-item[data-index=1]').click();
                       expect(Backbone.history.navigate).toHaveBeenCalledWith('test 2', {replace: true});
                   });

                   it('sets focus for screen readers', function () {
                       spyOn($.fn, 'focus');
                       view.$('.nav-item[data-index=1]').click();
                       expect(view.$('.sr-is-focusable.sr-tab').focus).toHaveBeenCalled();
                   });
               });
           }
          );
}).call(this, define || RequireJS.define);
