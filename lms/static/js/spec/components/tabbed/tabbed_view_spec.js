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
                           return this;
                       }
                   }),
                   activeTab = function () {
                       return view.$('.page-content-nav');
                   },
                   activeTabPanel = function () {
                       return view.$('.tabpanel[aria-expanded="true"]');
                   };

               describe('TabbedView component', function () {
                   beforeEach(function () {
                       view = new TabbedView({
                           tabs: [{
                               title: 'Test 1',
                               view: new TestSubview({text: 'this is test text'}),
                               url: 'test-1'
                           }, {
                               title: 'Test 2',
                               view: new TestSubview({text: 'other text'}),
                               url: 'test-2'
                           }]
                       }).render();

                       // _.defer() is used to make calls to
                       // jQuery.focus() work in Chrome.  _.defer()
                       // delays the execution of a function until the
                       // current call stack is clear.  That behavior
                       // will cause tests to fail, so we'll instead
                       // make _.defer() immediately invoke its
                       // argument.
                       spyOn(_, 'defer').andCallFake(function (func) {
                           func();
                       });
                   });

                   it('can render itself', function () {
                       expect(view.$el.html()).toContain('<nav class="page-content-nav"');
                   });

                   it('shows its first tab by default', function () {
                       expect(activeTabPanel().text()).toContain('this is test text');
                       expect(activeTabPanel().text()).not.toContain('other text');
                   });

                   it('displays titles for each tab', function () {
                       expect(activeTab().text()).toContain('Test 1');
                       expect(activeTab().text()).toContain('Test 2');
                   });

                   it('can switch tabs', function () {
                       view.$('.nav-item[data-index=1]').click();
                       expect(activeTabPanel().text()).not.toContain('this is test text');
                       expect(activeTabPanel().text()).toContain('other text');
                   });

                   it('marks the active tab as selected using aria attributes', function () {
                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr('aria-expanded', 'true');
                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr('aria-expanded', 'false');
                       view.$('.nav-item[data-index=1]').click();
                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr('aria-expanded', 'false');
                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr('aria-expanded', 'true');
                   });

                   it('sets focus for screen readers', function () {
                       spyOn($.fn, 'focus');
                       view.$('.nav-item[data-url="test-2"]').click();
                       expect(view.$('.sr-is-focusable.test-2').focus).toHaveBeenCalled();
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
