(function(define) {
    'use strict';

    define(['jquery',
            'underscore',
            'backbone',
            'common/js/components/views/tabbed_view',
            'jquery.simulate'
           ],
           function($, _, Backbone, TabbedView) {
               var keys = $.simulate.keyCode;

               var view,
                   TestSubview = Backbone.View.extend({
                       initialize: function(options) {
                           this.text = options.text;
                       },

                       render: function() {
                           this.$el.text(this.text);
                           return this;
                       }
                   }),
                   activeTab = function() {
                       return view.$('.page-content-nav');
                   },
                   activeTabPanel = function() {
                       return view.$('.tabpanel[aria-hidden="false"]');
                   };

               describe('TabbedView component', function() {
                   beforeEach(function() {
                       view = new TabbedView({
                           tabs: [{
                               title: 'Test 1',
                               view: new TestSubview({text: 'this is test text'}),
                               url: 'test-1'
                           }, {
                               title: 'Test 2',
                               view: new TestSubview({text: 'other text'}),
                               url: 'test-2'
                           }],
                           viewLabel: 'Tabs'
                       }).render();
                   });

                   it('can render itself', function() {
                       expect(view.$el.html()).toContain('<div class="page-content-nav"');
                   });

                   it('shows its first tab by default', function() {
                       expect(activeTabPanel().text()).toContain('this is test text');
                       expect(activeTabPanel().text()).not.toContain('other text');
                   });

                   it('displays titles for each tab', function() {
                       expect(activeTab().text()).toContain('Test 1');
                       expect(activeTab().text()).toContain('Test 2');
                   });

                   it('can switch tabs', function() {
                       view.$('.nav-item[data-index=1]').click();
                       expect(activeTabPanel().text()).not.toContain('this is test text');
                       expect(activeTabPanel().text()).toContain('other text');
                   });

                   it('marks the active tab as selected using aria attributes', function() {
                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr({
                           'aria-expanded': 'true',
                           'aria-selected': 'true',
                           'tabindex': '0'
                       });
                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr({
                           'aria-expanded': 'false',
                           'aria-selected': 'false',
                           'tabindex': '-1'
                       });
                       view.$('.nav-item[data-index=1]').click();
                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr({
                           'aria-expanded': 'false',
                           'aria-selected': 'false',
                           'tabindex': '-1'
                       });
                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr({
                           'aria-expanded': 'true',
                           'aria-selected': 'true',
                           'tabindex': '0'
                       });
                   });

                   it('works with keyboard navigation RIGHT and ENTER', function() {
                       view.$('.nav-item[data-index=0]').focus();
                       view.$('.nav-item[data-index=0]')
                        .simulate('keydown', {keyCode: keys.RIGHT})
                        .simulate('keydown', {keyCode: keys.ENTER});

                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr({
                           'aria-expanded': 'false',
                           'aria-selected': 'false',
                           'tabindex': '-1'
                       });
                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr({
                           'aria-expanded': 'true',
                           'aria-selected': 'true',
                           'tabindex': '0'
                       });
                   });

                   it('works with keyboard navigation DOWN and ENTER', function() {
                       view.$('.nav-item[data-index=0]').focus();
                       view.$('.nav-item[data-index=0]')
                        .simulate('keydown', {keyCode: keys.DOWN})
                        .simulate('keydown', {keyCode: keys.ENTER});

                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr({
                           'aria-expanded': 'false',
                           'aria-selected': 'false',
                           'tabindex': '-1'
                       });
                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr({
                           'aria-expanded': 'true',
                           'aria-selected': 'true',
                           'tabindex': '0'
                       });
                   });

                   it('works with keyboard navigation LEFT and ENTER', function() {
                       view.$('.nav-item[data-index=1]').focus();
                       view.$('.nav-item[data-index=1]')
                        .simulate('keydown', {keyCode: keys.LEFT})
                        .simulate('keydown', {keyCode: keys.ENTER});

                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr({
                           'aria-expanded': 'false',
                           'aria-selected': 'false',
                           'tabindex': '-1'
                       });
                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr({
                           'aria-expanded': 'true',
                           'aria-selected': 'true',
                           'tabindex': '0'
                       });
                   });

                   it('works with keyboard navigation UP and ENTER', function() {
                       view.$('.nav-item[data-index=1]').focus();
                       view.$('.nav-item[data-index=1]')
                        .simulate('keydown', {keyCode: keys.UP})
                        .simulate('keydown', {keyCode: keys.ENTER});

                       expect(view.$('.nav-item[data-index=1]')).toHaveAttr({
                           'aria-expanded': 'false',
                           'aria-selected': 'false',
                           'tabindex': '-1'
                       });
                       expect(view.$('.nav-item[data-index=0]')).toHaveAttr({
                           'aria-expanded': 'true',
                           'aria-selected': 'true',
                           'tabindex': '0'
                       });
                   });
               });
           });
}).call(this, define || RequireJS.define);
