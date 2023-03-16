import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import AlertListView, { mapAlertTypeToAlertHOF } from './program_alert_list_view';

import programListHeaderTpl from '../../../templates/learner_dashboard/program_list_header_view.underscore';

class ProgramListHeaderView extends Backbone.View {
    constructor(options) {
        const defaults = {
            el: '.js-program-list-header',
        };
        super(Object.assign({}, defaults, options));
    }

    initialize(options) {
        this.tpl = HtmlUtils.template(programListHeaderTpl);
        this.data = options.context;
        this.alertCollection = new Backbone.Collection(
            // TODO: get this from api
            this.data.programsData
                .map((programData) => (
                    [
                        { type: 'no_enrollment' },
                        { type: 'subscription_trial_expiring' },
                    ].map(mapAlertTypeToAlertHOF(
                        'program_list',
                        programData,
                        programData.subscription_data,
                    ))
                ))
                .flat()
        );
    }

    render() {
        HtmlUtils.setHtml(this.$el, this.tpl(this.data));
        this.postRender();
    }

    postRender() {
        if (this.alertCollection.length > 0) {
            this.alertListView = new AlertListView({
                el: '.js-program-list-alerts',
                alertCollection: this.alertCollection,
            });
        }
    }
}

export default ProgramListHeaderView;
