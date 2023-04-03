/* globals setFixtures */

import ProgramAlertListView, { mapAlertTypeToAlertHOF } from '../views/program_alert_list_view';

describe('Program Alert List View', () => {
    let view = null;

    const programData = {
        title: 'Test Program',
    };

    const subscriptionData = {
        is_eligible_for_subscription: true,
        subscription_price: '$39',
        subscription_start_date: '2023-03-18',
        subscription_state: 'active',
        trial_end_date: '2023-03-18',
        trial_end_time: '3:54 pm',
        trial_length: 7,
    };

    const alertList = [
        { type: 'no_enrollment' },
        { type: 'subscription_trial_expiring' },
    ];

    beforeEach(() => {
        setFixtures('<div class="js-program-details-alerts"></div>');
        view = new ProgramAlertListView({
            el: '.js-program-details-alerts',
            alertCollection: new Backbone.Collection(
                alertList.map(
                    mapAlertTypeToAlertHOF(
                        'program_details',
                        programData,
                        subscriptionData
                    )
                )
            ),
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
        expect(view.$('.alert:first .alert-heading').text().trim()).toEqual(`Enroll in a ${programData.title} course`);
        expect(view.$('.alert:first .alert-message').text().trim()).toEqual(`You have an active subscription to the ${programData.title} program but are not enrolled in any courses. Enroll in a remaining course and enjoy verified access.`);
    });

    it('should render subscription trial is expiring alert', () => {
        expect(view.$('.alert:last .alert-heading')).toContainText(/Subscription trial expires in.*Day/);
        expect(view.$('.alert:last .alert-message')).toContainText(`Your ${programData.title} trial will expire`);
        expect(view.$('.alert:last .alert-message')).toContainText(`and the card on file will be charged ${subscriptionData.subscription_price}/mos.`);
    });
});
