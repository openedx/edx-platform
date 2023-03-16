import Backbone from 'backbone';
import moment from 'moment';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import programAlertTpl from '../../../templates/learner_dashboard/program_alert_list_view.underscore';

// Maps an alert type to an alert object
// TODO: move this function to a better place
export function mapAlertTypeToAlertHOF(pageType, programData, subscriptionData) {
    return function ({ type: alertType }) {
        if (alertType === 'no_enrollment') {
            const values = {
                programName: programData.title,
            };

            return {
                title: StringUtils.interpolate(
                    gettext('Enroll in a {programName} course'),
                    values,
                ),
                message: pageType === 'program_details'
                    ? StringUtils.interpolate(
                        gettext('You have an active subscription to the {programName} program but are not enrolled in any courses. Enroll in a remaining course and enjoy verified access.'),
                        values,
                    )
                    : HtmlUtils.interpolateHtml(
                        gettext('According to our records, you are not enrolled in any courses included in your {programName} program subscription. Enroll in a course from the {i_start}Program Details{i_end} page.'),
                        {
                            ...values,
                            i_start: HtmlUtils.HTML('<i>'),
                            i_end: HtmlUtils.HTML('</i>'),
                        },
                    ),
                ...(pageType === 'program_list' && {
                    url: programData.detail_url,
                    urlText: gettext('View program'),
                }),
            };
        } else if (alertType === 'subscription_trial_expiring') {
            const title = 'Subscription trial expires in {remainingDays} Day';
            const message = 'Your {programName} trial will expire in {remainingDays} day at {trialEndTime} on {trialEndDate} and the card on file will be charged {subscriptionPrice}/mos.';
            const remainingDays = moment(
                subscriptionData.trial_end_date,
                'YYYY-MM-DD',
            ).diff(moment(), 'days');

            return {
                title: StringUtils.interpolate(
                    ngettext(title, title.replace(/\bDay\b/, 'Days'), remainingDays),
                    { remainingDays },
                ),
                message: StringUtils.interpolate(
                    ngettext(message, message.replace(/\bday\b/, 'days'), remainingDays),
                    {
                        remainingDays,
                        programName: programData.title,
                        trialEndTime: subscriptionData.trial_end_time,
                        trialEndDate: moment(subscriptionData.trial_end_date, 'YYYY-MM-DD').format('MMMM DD, YYYY'),
                        subscriptionPrice: subscriptionData.subscription_price,
                    },
                ),
            };
        }
    };
}

class ProgramAlertListView extends Backbone.View {
    constructor(options) {
        const defaults = {
            el: '.js-program-details-alerts',
        };
        super(Object.assign({}, defaults, options));
    }

    initialize(options) {
        this.tpl = HtmlUtils.template(programAlertTpl);
        this.alertCollection = options.alertCollection;
        this.render();
    }

    render() {
        const data = {
            alertList: this.alertCollection.toJSON(),
        };
        HtmlUtils.setHtml(this.$el, this.tpl(data));
    }
}

export default ProgramAlertListView;
