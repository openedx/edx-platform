define(['jquery',
    'underscore',
    'teams/js/views/topic_card',
    'teams/js/models/topic'],
function($, _, TopicCardView, Topic) {
    'use strict';

    describe('Topic card view', function() {
        var createTopicCardView = function() {
            return new TopicCardView({
                model: new Topic({
                    id: 'renewables',
                    name: 'Renewable Energy',
                    description: 'Explore how changes in <ⓡⓔⓝⓔⓦⓐⓑⓛⓔ> ʎƃɹǝuǝ will affect our lives.',
                    team_count: 34,
                    max_team_size: 20
                })
            });
        };

        beforeEach(function() {
            spyOn(TopicCardView.prototype, 'action');
        });

        it('can render itself', function() {
            var view = createTopicCardView();
            expect(view.$el).toHaveClass('square-card');
            expect(view.$el.find('.card-title').text()).toContain('Renewable Energy');
            expect(view.$el.find('.card-description').text()).toContain('changes in <ⓡⓔⓝⓔⓦⓐⓑⓛⓔ> ʎƃɹǝuǝ');
            expect(view.$el.find('.card-meta').text()).toContain('34 Teams');
            expect(view.$el.find('.action .sr').text()).toContain('View Teams in the Renewable Energy Topic');
        });

        it('navigates when action button is clicked', function() {
            var view = createTopicCardView();
            view.$el.find('.action').trigger('click');
            // TODO test actual navigation once implemented
            expect(view.action).toHaveBeenCalled();
        });
    });
}
);
