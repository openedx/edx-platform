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
                       view = new TabbedView({
                           tabs: [{
                               title: 'Test 1',
                               view: new TestSubview({text: 'this is test text'})
                           }, {
                               title: 'Test 2',
                               view: new TestSubview({text: 'other text'})
                           }]
                       }).render();
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

                   it('marks the active tab as selected using aria attributes', function () {
                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr('aria-selected', 'true');
                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr('aria-selected', 'false');
                       view.$('.nav-item[data-index=1]').click();
                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr('aria-selected', 'false');
                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr('aria-selected', 'true');
                   });

                   it('sets focus for screen readers', function () {
                       spyOn($.fn, 'focus');
                       view.$('.nav-item[data-index=1]').click();
                       expect(view.$('.sr-is-focusable.sr-tab').focus).toHaveBeenCalled();
                   });

                   describe('history', function() {
                       beforeEach(function () {
                           spyOn(Backbone.history, 'navigate').andCallThrough();
                           view = new TabbedView({
                               tabs: [{
                                   url: 'test 1',
                                   title: 'Test 1',
                                   view: new TestSubview({text: 'this is test text'})
                               }, {
                                   url: 'test 2',
                                   title: 'Test 2',
                                   view: new TestSubview({text: 'other text'})
                               }],
                               router: new Backbone.Router({
                                   routes: {
                                       'test 1': function () {
                                           view.setActiveTab(0);
                                       },
                                       'test 2': function () {
                                           view.setActiveTab(1);
                                       }
                                   }
                               })
                           }).render();
                           Backbone.history.start();
                       });

                       afterEach(function () {
                           view.router.navigate('');
                           Backbone.history.stop();
                       });

                       it('updates the page URL on tab switches without adding to browser history', function () {
                           view.$('.nav-item[data-index=1]').click();
                           expect(Backbone.history.navigate).toHaveBeenCalledWith(
                               'test 2',
                               {replace: true}
                           );
                       });

                       it('changes tabs on URL navigation', function () {
                           expect(view.$('.nav-item.is-active').data('index')).toEqual(0);
                           Backbone.history.navigate('test 2', {trigger: true});
                           expect(view.$('.nav-item.is-active').data('index')).toEqual(1);
                       });
                   });

               });
           });
}).call(this, define || RequireJS.define);
