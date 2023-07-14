/* globals setFixtures */

import Backbone from 'backbone';

import ProgressCollection from '../collections/program_progress_collection';
import ProgramListHeaderView from '../views/program_list_header_view';

describe('Program List Header View', () => {
    let view = null;
    const context = {
        programsData: [
            {
                uuid: '5b234e3c-3a2e-472e-90db-6f51501dc86c',
                title: 'edX Demonstration Program',
                subscription_eligible: null,
                subscription_prices: [],
                detail_url: '/dashboard/programs/5b234e3c-3a2e-472e-90db-6f51501dc86c/',
            },
            {
                uuid: 'b90d70d5-f981-4508-bdeb-5b792d930c03',
                title: 'Test Program',
                subscription_eligible: true,
                subscription_prices: [{ price: '500.00', currency: 'USD' }],
                detail_url: '/dashboard/programs/b90d70d5-f981-4508-bdeb-5b792d930c03/',
            },
        ],
        programsSubscriptionData: [
            {
                id: 'eeb25640-9741-4c11-963c-8a27337f217c',
                resource_id: 'b90d70d5-f981-4508-bdeb-5b792d930c03',
                trial_end: '2022-04-20T05:59:42Z',
                current_period_end: '2023-05-08T05:59:42Z',
                subscription_state: 'active',
            },
        ],
        userProgress: [
            {
                uuid: '5b234e3c-3a2e-472e-90db-6f51501dc86c',
                completed: 0,
                in_progress: 1,
                not_started: 0,
                all_unenrolled: false,
            },
            {
                uuid: 'b90d70d5-f981-4508-bdeb-5b792d930c03',
                completed: 0,
                in_progress: 0,
                not_started: 3,
                all_unenrolled: true,
            },
        ],
        isUserB2CSubscriptionsEnabled: true,
    };

    beforeEach(() => {
        context.subscriptionCollection = new Backbone.Collection(
            context.programsSubscriptionData
        );
        context.progressCollection = new ProgressCollection(
            context.userProgress
        );
        setFixtures('<div class="js-program-list-header"></div>');
        view = new ProgramListHeaderView({
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

    it('should render the program heading', () => {
        expect(view.$('h2:first').text().trim()).toEqual('My programs');
    });

    it('should render a program alert', () => {
        expect(
            view.$('.js-program-list-alerts .alert .alert-heading').html().trim()
        ).toEqual('Enroll in a Test Program\'s course');
        expect(
            view.$('.js-program-list-alerts .alert .alert-message')
        ).toContainHtml(
            'According to our records, you are not enrolled in any courses included in your Test Program program subscription. Enroll in a course from the <i>Program Details</i> page.'
        );
        expect(
            view.$('.js-program-list-alerts .alert .view-button').attr('href')
        ).toEqual('/dashboard/programs/b90d70d5-f981-4508-bdeb-5b792d930c03/');
    });
});
