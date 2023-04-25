import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import upgradeMessageTpl from '../../../templates/learner_dashboard/upgrade_message.underscore';
import trackECommerceEvents from '../../commerce/track_ecommerce_events';

class UpgradeMessageView extends Backbone.View {
    initialize(options) {
        this.messageTpl = HtmlUtils.template(upgradeMessageTpl);
        this.$el = options.$el;
        this.render();

        const courseUpsellButtons = this.$el.find('.program_dashboard_course_upsell_button');
        trackECommerceEvents.trackUpsellClick(courseUpsellButtons, 'program_dashboard_course', {
            linkType: 'button',
            pageName: 'program_dashboard',
            linkCategory: 'green_upgrade',
        });
    }

    render() {
        const data = this.model.toJSON();
        HtmlUtils.setHtml(this.$el, this.messageTpl(data));
    }
}

export default UpgradeMessageView;
