/* globals setFixtures */

import ProgramListHeaderView from '../views/program_list_header_view';

describe('Program List Header View', () => {
    let view = null;
    const context = {
        programsData: [
            {
                title: 'Program 1',
                subscription_data: {
                    is_eligible_for_subscription: true,
                    subscription_price: '$39',
                    subscription_start_date: '2023-03-18',
                    subscription_state: 'active',
                    trial_end_date: '2023-03-18',
                    trial_end_time: '3:54 pm',
                    trial_length: 7,
                },
            },
        ],
    };

    beforeEach(() => {
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
        expect(view.$('h2:first').text().trim()).toEqual('Your programs');
    });

    it('should render the program alerts if there are alerts', () => {
        // TODO: update this test after api integration
        expect(view.$('.js-program-list-alerts .alert')[0]).toBeInDOM();
    });
});
