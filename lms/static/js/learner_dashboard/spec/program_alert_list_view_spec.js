/* globals setFixtures */

import ProgramAlertListView from '../views/program_alert_list_view';

describe('Program Alert List View', () => {
    let view = null;
    const context = {
        enrollmentAlerts: [{ title: 'Test Program' }],
        trialEndingAlerts: [{
            title: 'Test Program',
            hasActiveTrial: true,
            currentPeriodEnd: 'May 8, 2023',
            remainingDays: 2,
            subscriptionPrice: '$100/month USD',
            subscriptionState: 'active',
            subscriptionUrl: null,
            trialEndDate: 'Apr 20, 2023',
            trialEndTime: '5:59 am',
            trialLength: 7,
        }],
        pageType: 'programDetails',
    };

    beforeEach(() => {
        setFixtures('<div class="js-program-details-alerts"></div>');
        view = new ProgramAlertListView({
            el: '.js-program-details-alerts',
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

    it('should render no enrollement alert', () => {
        expect(view.$('.alert:first .alert-heading').text().trim()).toEqual(
            'Enroll in a Test Program\'s course'
        );
        expect(view.$('.alert:first .alert-message').text().trim()).toEqual(
            'You have an active subscription to the Test Program program but are not enrolled in any courses. Enroll in a remaining course and enjoy verified access.'
        );
    });

    it('should render subscription trial is expiring alert', () => {
        expect(view.$('.alert:last .alert-heading').text().trim()).toEqual(
            'Subscription trial expires in 2 days'
        );
        expect(view.$('.alert:last .alert-message').text().trim()).toEqual(
            'Your Test Program trial will expire in 2 days at 5:59 am on Apr 20, 2023 and the card on file will be charged $100/month USD.'
        );
    });
});
