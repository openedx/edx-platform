define(['jquery',
        'underscore',
        'teams/js/views/topic_card',
        'teams/js/models/topic'],
    function ($, _, TopicCardView, Topic) {

        describe('topic card view', function () {
            var view;

            beforeEach(function () {
                spyOn(TopicCardView.prototype, 'action');
                view = new TopicCardView({
                    model: new Topic({
                        'id': 'renewables',
                        'name': 'Renewable Energy',
                        'description': 'Explore how changes in <ⓡⓔⓝⓔⓦⓐⓑⓛⓔ> ʎƃɹǝuǝ will affect our lives.',
                        'team_count': 34
                    })
                });
            });

            it('can render itself', function () {
                expect(view.$el).toHaveClass('square-card');
                expect(view.$el.find('.card-title').text()).toContain('Renewable Energy');
                expect(view.$el.find('.card-description').text()).toContain('changes in <ⓡⓔⓝⓔⓦⓐⓑⓛⓔ> ʎƃɹǝuǝ');
                expect(view.$el.find('.card-meta').text()).toContain('34 Teams');
                expect(view.$el.find('.action .sr').text()).toContain('View Teams in the Renewable Energy Topic');
            });

            it('navigates when action button is clicked', function () {
                view.$el.find('.action').trigger('click');
                // TODO test actual navigation once implemented
                expect(view.action).toHaveBeenCalled();
            });
        });
    }
);
