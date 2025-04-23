/* globals setFixtures */

import Backbone from 'backbone';

import ProgressCollection from '../collections/program_progress_collection';
// eslint-disable-next-line import/no-named-as-default, import/no-named-as-default-member
import ProgramListHeaderView from '../views/program_list_header_view';

describe('Program List Header View', () => {
    let view = null;
    const context = {
        programsData: [
            {
                uuid: '5b234e3c-3a2e-472e-90db-6f51501dc86c',
                title: 'edX Demonstration Program',
                detail_url: '/dashboard/programs/5b234e3c-3a2e-472e-90db-6f51501dc86c/',
            },
            {
                uuid: 'b90d70d5-f981-4508-bdeb-5b792d930c03',
                title: 'Test Program',
                detail_url: '/dashboard/programs/b90d70d5-f981-4508-bdeb-5b792d930c03/',
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
    };

    beforeEach(() => {
        context.progressCollection = new ProgressCollection(
            context.userProgress,
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
});
