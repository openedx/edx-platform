(function (define) {
    'use strict';

    define(['jquery',
            'underscore',
            'js/components/header/views/header',
            'js/components/header/models/header'
           ],
           function($, _, HeaderView, HeaderModel) {

               describe('header component view', function () {
                   var model, view;

                   var testBreadcrumbs = function (breadcrumbs) {
                       model.set('breadcrumbs', breadcrumbs);
                       expect(view.$('nav.breadcrumbs').length).toBe(1);
                       _.each(view.$('.nav-item'), function (el, index) {
                           expect($(el).attr('href')).toEqual(breadcrumbs[index].url);
                           expect($(el).text()).toEqual(breadcrumbs[index].title);
                       });
                   };

                   beforeEach(function () {
                       model = new HeaderModel({
                           title: 'Test title',
                           description: 'Test description'
                       });
                       view = new HeaderView({
                           model: model
                       });
                   });

                   it('can render itself', function () {
                       expect(view.$el.text()).toContain('Test title');
                       expect(view.$el.text()).toContain('Test description');
                   });

                   it('does not show breadcrumbs by default', function () {
                       expect(view.$el.html()).not.toContain('<nav class="breadcrumbs">');
                   });

                   it('shows breadcrumbs if they are supplied', function () {
                       testBreadcrumbs([
                           {url: 'url1', title: 'Crumb 1'},
                           {url: 'url2', title: 'Crumb 2'}
                       ]);
                       testBreadcrumbs([{url: 'url1', title: 'Crumb 1'}]);
                   });

                   it('renders itself when its model changes', function () {
                       expect(view.$el.text()).toContain('Test title');
                       model.set('title', 'Changed title');
                       expect(view.$el.text()).toContain('Changed title');
                   });
               });
           }
          );
}).call(this, define || RequireJS.define);
