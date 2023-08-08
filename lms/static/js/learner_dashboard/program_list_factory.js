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
    const subscriptionCollection = new Backbone.Collection();

    if (options.userProgress) {
        progressCollection.set(options.userProgress);
        options.progressCollection = progressCollection; // eslint-disable-line no-param-reassign
    }

    if (options.programsSubscriptionData.length) {
        subscriptionCollection.set(options.programsSubscriptionData);
        options.subscriptionCollection = subscriptionCollection; // eslint-disable-line no-param-reassign
    }

    if (options.programsData.length) {
        if (!options.mobileOnly) {
            new HeaderView({
                context: options,
            }).render();
        }

        const activeSubscriptions = options.programsSubscriptionData
            // eslint-disable-next-line camelcase
            .filter(({ subscription_state }) => subscription_state === 'active')
            .sort((a, b) => new Date(b.created) - new Date(a.created));

        // Sort programs so programs with active subscriptions are at the top
        if (activeSubscriptions.length) {
            // eslint-disable-next-line no-param-reassign
            options.programsData = options.programsData
                .map((programsData) => ({
                    ...programsData,
                    subscriptionIndex: activeSubscriptions.findIndex(
                        // eslint-disable-next-line camelcase
                        ({ resource_id }) => resource_id === programsData.uuid,
                    ),
                }))
                .sort(({ subscriptionIndex: indexA }, { subscriptionIndex: indexB }) => {
                    switch (true) {
                    case indexA === -1 && indexB === -1:
                        // Maintain the original order for non-subscription programs
                        return 0;
                    case indexA === -1:
                        // Move non-subscription program to the end
                        return 1;
                    case indexB === -1:
                        // Keep non-subscription program to the end
                        return -1;
                    default:
                        // Sort by subscriptionIndex in ascending order
                        return indexA - indexB;
                    }
                });
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
