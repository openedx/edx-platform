/* globals setFixtures */

import SidebarView from '../views/sidebar_view';

describe('Sidebar View', () => {
    let view = null;
    const context = {
        marketingUrl: 'https://www.example.org/programs',
        subscriptionUpsellData: {
            marketing_url: 'https://www.example.org/program-subscriptions',
            minimum_price: '$39',
            trial_length: 7,
        },
        isUserB2CSubscriptionsEnabled: true,
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

    it('should not render the subscription upsell section', () => {
        expect(view.$('.js-subscription-upsell')[0]).not.toBeInDOM();
    });

    it('should load the exploration panel given a marketing URL', () => {
        expect(view.$('.program-advertise .advertise-message').html().trim())
            .toEqual(
                'Browse recently launched courses and see what\'s new in your favorite subjects',
            );
        expect(view.$('.program-advertise a').attr('href'))
            .toEqual(context.marketingUrl);
    });

    it('should not load the advertising panel if no marketing URL is provided', () => {
        view.remove();
        view = new SidebarView({
            el: '.sidebar',
            context: {
                isUserB2CSubscriptionsEnabled: true,
                subscriptionUpsellData: context.subscriptionUpsellData,
            },
        });
        view.render();
        const $ad = view.$el.find('.program-advertise');
        expect($ad.length).toBe(0);
    });
});
