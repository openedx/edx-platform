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

    it('should load the exploration panel given a marketing URL', () => {
        const $sidebar = view.$el;
        expect($sidebar.find('.program-advertise .advertise-message').html().trim())
            .toEqual('Browse recently launched courses and see what\'s new in your favorite subjects');
        expect($sidebar.find('.program-advertise .ad-link a').attr('href')).toEqual(context.marketingUrl);
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
