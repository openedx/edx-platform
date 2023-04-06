/* globals setFixtures */

import SidebarView from '../views/sidebar_view';

describe('Sidebar View', () => {
    let view = null;
    const context = {
        marketingUrl: 'https://www.example.org/programs',
    };

    beforeEach(() => {
        setFixtures('<div class="sidebar"></div>');

        view = new SidebarView({
            el: '.sidebar',
            context,
        });
        view.render();
    });

    afterEach(() => {
        view.remove();
    });

    it('should exist', () => {
        expect(view).toBeDefined();
    });

    it('should render the subscription upsell section', () => {
        expect(view.$('.js-subscription-upsell')[0]).toBeInDOM();
        expect(view.$('.js-subscription-upsell .badge').html().trim())
            .toEqual('New');
        expect(view.$('.js-subscription-upsell h4').html().trim())
            .toEqual('Monthly program subscriptions now available');
        expect(view.$('.js-subscription-upsell .advertise-message'))
            .toContainText(
                'An easier way to access popular programs with more control over how much you spend.'
            );
        expect(view.$('.js-subscription-upsell a span:last').html().trim())
            .toEqual('Explore subscription options');
        expect(view.$('.js-subscription-upsell a').attr('href'))
            .not
            .toEqual(context.marketingUrl);
    });

    it('should load the exploration panel given a marketing URL', () => {
        expect(view.$('.program-advertise .advertise-message').html().trim())
            .toEqual(
                'Browse recently launched courses and see what\'s new in your favorite subjects'
            );
        expect(view.$('.program-advertise a').attr('href'))
            .toEqual(context.marketingUrl);
    });

    it('should not load the advertising panel if no marketing URL is provided', () => {
        view.remove();
        view = new SidebarView({
            el: '.sidebar',
            context: {},
        });
        view.render();
        const $ad = view.$el.find('.program-advertise');
        expect($ad.length).toBe(0);
    });
});
