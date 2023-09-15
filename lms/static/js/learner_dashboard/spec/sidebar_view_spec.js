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

    it('should not render the subscription upsell section if B2CSubscriptions are disabled', () => {
        view.remove();
        view = new SidebarView({
            el: '.sidebar',
            context: {
                ...context,
                isUserB2CSubscriptionsEnabled: false,
            },
        });
        view.render();
        expect(view.$('.js-subscription-upsell')[0]).not.toBeInDOM();
    });

    it('should render the subscription upsell section', () => {
        expect(view.$('.js-subscription-upsell')[0]).toBeInDOM();
        expect(view.$('.js-subscription-upsell .badge').html().trim())
            .toEqual('New');
        expect(view.$('.js-subscription-upsell h4').html().trim())
            .toMatch(/^Monthly program subscriptions . more flexible, more affordable$/);
        expect(view.$('.js-subscription-upsell .advertise-message').html().trim())
            .toEqual(
                'Now available for many popular programs, affordable monthly subscription pricing can help you manage your budget more effectively. Subscriptions start at $39/month USD per program, after a 7-day full access free trial. Cancel at any time.',
            );
        expect(view.$('.js-subscription-upsell a span:last').html().trim())
            .toEqual('Explore subscription options');
        expect(view.$('.js-subscription-upsell a').attr('href'))
            .toEqual('https://www.example.org/program-subscriptions');
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
