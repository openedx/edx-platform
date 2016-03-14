(function (define) {
    'use strict';

    define(['jquery',
            'underscore',
            'backbone',
            'js/components/card/views/card'
           ],
        function($, _, Backbone, CardView) {

            describe('card component view', function () {
                it('can render itself as a square card', function () {
                    var view = new CardView({ configuration: 'square_card' });
                    expect(view.$el).toHaveClass('square-card');
                    expect(view.$el.find('.wrapper-card-meta .action').length).toBe(1);
                });

                it('can render itself as a list card', function () {
                    var view = new CardView({ configuration: 'list_card' });
                    expect(view.$el).toHaveClass('list-card');
                    expect(view.$el.find('.wrapper-card-core .action').length).toBe(1);
                });

                it('renders a pennant only if the pennant value is truthy', function () {
                    var view = new (CardView.extend({ pennant: '' }))();
                    expect(view.$el.find('.card-type').length).toBe(0);
                    view = new (CardView.extend({ pennant: 'Test Pennant' }))();
                    expect(view.$el.find('.card-type').length).toBe(1);
                });

                it('can render child views', function () {
                    var testChildView = new (Backbone.View.extend({ className: 'test-view' }))();
                    spyOn(testChildView, 'render');
                    var view = new (CardView.extend({ details: [testChildView] }))();
                    expect(testChildView.render).toHaveBeenCalled();
                    expect(view.$el.find('.test-view')).toHaveClass('meta-detail');
                });

                it('calls action when clicked', function () {
                    spyOn(CardView.prototype, 'action');
                    var view = new CardView({ configuration: 'square_card' });
                    view.$el.find('.action').trigger('click');
                    expect(view.action).toHaveBeenCalled();
                });

                var verifyContent = function (view) {
                    expect(view.$el).toHaveClass('test-card');
                    expect(view.$el.find('.card-type').text()).toContain('Pennant');
                    expect(view.$el.find('.card-title').text()).toContain('A test title');
                    expect(view.$el.find('.card-description').text()).toContain('A test description');
                    expect(view.$el.find('.action')).toHaveClass('test-action');
                    expect(view.$el.find('.action')).toHaveAttr('href', 'www.example.com');
                    expect(view.$el.find('.action').text()).toContain('A test action');
                };

                it('can have strings for cardClass, pennant, title, description, and action', function () {
                    var view = new (CardView.extend({
                        cardClass: 'test-card',
                        pennant: 'Pennant',
                        title: 'A test title',
                        description: 'A test description',
                        actionClass: 'test-action',
                        actionUrl: 'www.example.com',
                        actionContent: 'A test action'
                    }))();
                    verifyContent(view);
                });

                it('can have functions for cardClass, pennant, title, description, and action', function () {
                    var view = new (CardView.extend({
                        cardClass: function () { return 'test-card'; },
                        pennant: function () { return 'Pennant'; },
                        title: function () { return 'A test title'; },
                        description: function () { return 'A test description'; },
                        actionClass: function () { return 'test-action'; },
                        actionUrl: function () { return 'www.example.com'; },
                        actionContent: function () { return 'A test action'; }
                    }));
                    verifyContent(view);
                });
            });
        });
}).call(this, define || RequireJS.define);
