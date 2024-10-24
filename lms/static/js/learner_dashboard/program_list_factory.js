import Backbone from 'backbone';

import CollectionListView from './views/collection_list_view';
// eslint-disable-next-line import/no-named-as-default, import/no-named-as-default-member
import ProgramCardView from './views/program_card_view';
import ProgramCollection from './collections/program_collection';
import ProgressCollection from './collections/program_progress_collection';
import SidebarView from './views/sidebar_view';
// eslint-disable-next-line import/no-named-as-default, import/no-named-as-default-member
import HeaderView from './views/program_list_header_view';

function ProgramListFactory(options) {
    const progressCollection = new ProgressCollection();

    if (options.userProgress) {
        progressCollection.set(options.userProgress);
        options.progressCollection = progressCollection; // eslint-disable-line no-param-reassign
    }

    if (options.programsData.length) {
        if (!options.mobileOnly) {
            new HeaderView({
                context: options,
            }).render();
        }
    }

    new CollectionListView({
        el: '.program-cards-container',
        childView: ProgramCardView,
        collection: new ProgramCollection(options.programsData),
        context: options,
    }).render();

    if (options.programsData.length) {
        new SidebarView({
            el: '.sidebar',
            context: options,
        }).render();
    }
}

export { ProgramListFactory }; // eslint-disable-line import/prefer-default-export
