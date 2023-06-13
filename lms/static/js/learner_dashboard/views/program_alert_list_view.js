import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import warningIcon from '../../../images/warning-icon.svg';
import programAlertTpl from '../../../templates/learner_dashboard/program_alert_list_view.underscore';

class ProgramAlertListView extends Backbone.View {
    constructor(options) {
        const defaults = {
            el: '.js-program-details-alerts',
        };
        super(Object.assign({}, defaults, options));
    }

    initialize({ context }) {
        this.tpl = HtmlUtils.template(programAlertTpl);
        this.enrollmentAlerts = context.enrollmentAlerts || [];
        this.trialEndingAlerts = context.trialEndingAlerts || [];
        this.pageType = context.pageType;
        this.render();
    }

    render() {
        const data = {
            alertList: this.getAlertList(),
            warningIcon,
        };
        HtmlUtils.setHtml(this.$el, this.tpl(data));
    }

    getAlertList() {
        const alertList = this.enrollmentAlerts.map(
            ({ title: programName, url }) => ({
                url,
                urlText: gettext('View program'),
                title: StringUtils.interpolate(
                    gettext('Enroll in a {programName}\'s course'),
                    { programName }
                ),
                message: this.pageType === 'programDetails'
                    ? StringUtils.interpolate(
                        gettext('You have an active subscription to the {programName} program but are not enrolled in any courses. Enroll in a remaining course and enjoy verified access.'),
                        { programName }
                    )
                    : HtmlUtils.interpolateHtml(
                        gettext('According to our records, you are not enrolled in any courses included in your {programName} program subscription. Enroll in a course from the {i_start}Program Details{i_end} page.'),
                        {
                            programName,
                            i_start: HtmlUtils.HTML('<i>'),
                            i_end: HtmlUtils.HTML('</i>'),
                        }
                    ),
            })
        );
        return alertList.concat(this.trialEndingAlerts.map(
            ({ title: programName, remainingDays, ...data }) => ({
                title: StringUtils.interpolate(
                    remainingDays < 1
                        ? gettext('Subscription trial expires in less than 24 hours')
                        : ngettext('Subscription trial expires in {remainingDays} day', 'Subscription trial expires in {remainingDays} days', remainingDays),
                    { remainingDays }
                ),
                message: StringUtils.interpolate(
                    remainingDays < 1
                        ? gettext('Your {programName} trial will expire at {trialEndTime} on {trialEndDate} and the card on file will be charged {subscriptionPrice}.')
                        : ngettext('Your {programName} trial will expire in {remainingDays} day at {trialEndTime} on {trialEndDate} and the card on file will be charged {subscriptionPrice}.', 'Your {programName} trial will expire in {remainingDays} days at {trialEndTime} on {trialEndDate} and the card on file will be charged {subscriptionPrice}.', remainingDays),
                    {
                        programName,
                        remainingDays,
                        ...data,
                    }
                ),
            })
        ));
    }
}

export default ProgramAlertListView;
