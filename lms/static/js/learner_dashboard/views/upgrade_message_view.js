import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import upgradeMessageTpl from '../../../templates/learner_dashboard/upgrade_message.underscore';
<<<<<<< HEAD
import upgradeMessageSubscriptionTpl from '../../../templates/learner_dashboard/upgrade_message_subscription.underscore';
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
import trackECommerceEvents from '../../commerce/track_ecommerce_events';

class UpgradeMessageView extends Backbone.View {
    initialize(options) {
<<<<<<< HEAD
        if (options.isSubscriptionEligible) {
            this.messageTpl = HtmlUtils.template(upgradeMessageSubscriptionTpl);
        } else {
            this.messageTpl = HtmlUtils.template(upgradeMessageTpl);
        }
        this.$el = options.$el;
        this.subscriptionModel = options.subscriptionModel;
=======
        this.messageTpl = HtmlUtils.template(upgradeMessageTpl);
        this.$el = options.$el;
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        this.render();

        const courseUpsellButtons = this.$el.find('.program_dashboard_course_upsell_button');
        trackECommerceEvents.trackUpsellClick(courseUpsellButtons, 'program_dashboard_course', {
            linkType: 'button',
            pageName: 'program_dashboard',
            linkCategory: 'green_upgrade',
        });
    }

    render() {
        // eslint-disable-next-line no-undef
        const data = $.extend(
            {},
            this.model.toJSON(),
<<<<<<< HEAD
            this.subscriptionModel.toJSON(),
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        );
        HtmlUtils.setHtml(this.$el, this.messageTpl(data));
    }
}

export default UpgradeMessageView;
