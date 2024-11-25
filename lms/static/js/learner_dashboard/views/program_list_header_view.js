import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

<<<<<<< HEAD
import AlertListView from './program_alert_list_view';

import SubscriptionModel from '../models/program_subscription_model';

=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
import programListHeaderTpl from '../../../templates/learner_dashboard/program_list_header_view.underscore';

class ProgramListHeaderView extends Backbone.View {
    constructor(options) {
        const defaults = {
            el: '.js-program-list-header',
        };
        super(Object.assign({}, defaults, options));
    }

    initialize({ context }) {
        this.context = context;
        this.tpl = HtmlUtils.template(programListHeaderTpl);
<<<<<<< HEAD
        this.programAndSubscriptionData = context.programsData
            .map((programData) => ({
                programData,
                subscriptionData: context.subscriptionCollection
                    ?.findWhere({
                        resource_id: programData.uuid,
                        subscription_state: 'active',
                    })
                    ?.toJSON(),
            }))
            .filter(({ subscriptionData }) => !!subscriptionData);
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        this.render();
    }

    render() {
        HtmlUtils.setHtml(this.$el, this.tpl(this.context));
<<<<<<< HEAD
        this.postRender();
    }

    postRender() {
        if (this.context.isUserB2CSubscriptionsEnabled) {
            const enrollmentAlerts = this.getEnrollmentAlerts();
            const trialEndingAlerts = this.getTrialEndingAlerts();

            if (enrollmentAlerts.length || trialEndingAlerts.length) {
                this.alertListView = new AlertListView({
                    el: '.js-program-list-alerts',
                    context: {
                        enrollmentAlerts,
                        trialEndingAlerts,
                        pageType: 'programList',
                    },
                });
            }
        }
    }

    getEnrollmentAlerts() {
        return this.programAndSubscriptionData
            .map(({ programData, subscriptionData }) =>
                this.context.progressCollection?.findWhere({
                    uuid: programData.uuid,
                    all_unenrolled: true,
                }) ? {
                    title: programData.title,
                    url: programData.detail_url,
                } : null
            )
            .filter(Boolean);
    }

    getTrialEndingAlerts() {
        return this.programAndSubscriptionData
            .map(({ programData, subscriptionData }) => {
                const subscriptionModel = new SubscriptionModel({
                    context: {
                        programData,
                        subscriptionData: [subscriptionData],
                        userPreferences: this.context?.userPreferences,
                    },
                });
                return (
                    subscriptionModel.get('remainingDays') <= 7 &&
                    subscriptionModel.get('hasActiveTrial') && {
                        title: programData.title,
                        ...subscriptionModel.toJSON(),
                    }
                );
            })
            .filter(Boolean);
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    }
}

export default ProgramListHeaderView;
